from pydrive.auth import GoogleAuth

gauth = GoogleAuth()

print ("Authenticating, a web browser may be opened")
if gauth.credentials is None:
    # Authenticate if they're not there
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresh them if expired
    gauth.Refresh()
else:
    # Initialize the saved creds
    gauth.Authorize()

print("Authenication complete, you should now have a 'credentials.json' file")

print("Check the connection is correct by checking that there is a 'wildpi' folder in your google drive")

from pydrive.drive import GoogleDrive
drive = GoogleDrive(gauth)

# Auto-iterate through all files that matches this query
file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
for file1 in file_list:
    if file1['title'] == 'wildpi': 
        print('title: %s, id: %s' % (file1['title'], file1['id']))
