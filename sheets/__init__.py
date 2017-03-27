from oauth2client.service_account import ServiceAccountCredentials

import httplib2

from apiclient import discovery

SCOPES = 'https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive'

DISCOVERY_URL = 'https://sheets.googleapis.com/$discovery/rest?version=v4'

SPREADSHEET_LINK_TMPL = "https://docs.google.com/spreadsheets/d/%s/edit"


class Service(object):
    def __init__(self, creds):
        http = creds.authorize(httplib2.Http())

        self.drive = discovery.build('drive', 'v3', http=http)
        self.sheets = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URL)


def _get_credentials(creds_file_name):
    return ServiceAccountCredentials.from_json_keyfile_name(creds_file_name, SCOPES)


def get_sheets_service(creds_file_name):
    creds = _get_credentials(creds_file_name)
    return Service(creds)


def get_file_by_name(service, name):
    result = service.drive.files().list(q="name='%s'" % name).execute()

    if not result['files']:
        return None

    return result['files'][0]


def create_spreadsheet(service, name):
    spreadsheet_body = {
        "properties": {"title": name}
    }

    request = service.sheets.spreadsheets().create(body=spreadsheet_body)
    response = request.execute()

    return response


def get_or_create_ss(service, name):
    ss = get_file_by_name(service, name)

    if ss:
        ss_id = ss['id']
    else:
        ss_props = create_spreadsheet(service, name)
        ss_id = ss_props['spreadsheetId']

    return ss_id


def append_cells(service, ss_id, data):
    req = service.sheets.spreadsheets().values().append(
        spreadsheetId=ss_id,
        # TODO: This is a magic number for now
        range="A1:D",
        valueInputOption="USER_ENTERED",
        body={"range": "A1:D",
              "majorDimension": "ROWS",
              "values": data})

    return req.execute()


def share_file(service, file_id, user_email):
    user_permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': user_email
    }

    result = service.drive.permissions().create(fileId=file_id,
                                                body=user_permission,
                                                fields='id').execute()

    return result


def get_link(ss_id):
    return SPREADSHEET_LINK_TMPL % ss_id