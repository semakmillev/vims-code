from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from vims_code.models.api import DatabaseConnection
from vims_code.models.code_list import CodeList
from vims_code.models.code_param_value_list import CodeParamValueList
from vims_code.models.code_value_list import CodeValueList

client_id = "230650962852-dg1o1aha21j8bbchh4tcn3kljiubgash.apps.googleusercontent.com"
client_secret = "vIOLakWyEWY3vK_pCQCcC_5I"

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


# The ID and range of a sample spreadsheet.
# SAMPLE_SPREADSHEET_ID = '18ZqNl7of5YKx2pF9J6BZ1BoBnEDEDiwbRlvUQqQdTVk'


def load_code(conn: DatabaseConnection,
              code_id: int,
              caption: str,
              level_id: int,
              code_type: str,
              code_value: str,
              points: int,
              penalty: str,
              bonus: str,
              time_from: str,
              time_to: str,
              additional_params: {}):
    cl = CodeList(conn)
    code_id = cl.set(code_id, caption, points, code_type)
    print(code_id)
    cvl = CodeValueList(conn)
    cvl.delete_by_code(code_id)
    if code_type == "ТЕКСТ":
        code_values = code_value.split("#")
        for cv in code_values:
            cvl.set(None, code_id=code_id, value_type="ТЕКСТ", code_value=cv)
    cpvl = CodeParamValueList(conn)
    cpvl.delete_by_code(code_id)
    cpvl.set(None, code_id, "ШТРАФ", 'NUMBER', penalty)
    cpvl.set(None, code_id, "БОНУС", 'NUMBER', bonus)
    cpvl.set(None, code_id, "ВРЕМЯ_С", 'NUMBER', time_from)
    cpvl.set(None, code_id, "ВРЕМЯ_ПО", 'NUMBER', time_to)
    for param_code in additional_params:
        cpvl.set(None, code_id, param_code, additional_params[param_code])
    return code_id


def load_codes(conn: DatabaseConnection, level_id: int, spreadsheet: str, sheet_name: str):
    creds = None
    main_range_name = f'{sheet_name}!main_params'
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet,
                                range=main_range_name).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        result_codes = [["_ID"]]
        value_dict_arr = [dict(zip(values[0], values[row_index])) for row_index in range(1, len(values))]
        for x in value_dict_arr:
            code_id = load_code(conn,
                                code_id=x.get('ID_') if x.get('ID_') != '' else None,
                                caption=x.get('ИМЯ'),
                                level_id=level_id,
                                code_type=x.get('ТИП'),
                                code_value=x.get('ЗНАЧЕНИЕ'),
                                points=x.get('ОЧКИ'),
                                penalty=x.get('ШТРАФ'),
                                bonus=x.get('БОНУС'),
                                time_from=x.get('ВРЕМЯ_С'),
                                time_to=x.get('ВРЕМЯ_ПО'),
                                additional_params={})
            result_codes.append([code_id])

        sheet.values().update(spreadsheetId=spreadsheet,
                              range=f'{sheet_name}!code_id', body={"values": result_codes},
                              valueInputOption='RAW').execute()
