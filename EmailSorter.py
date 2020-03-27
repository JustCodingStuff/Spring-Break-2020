from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient import errors

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://mail.google.com/"]


def get_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
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

    service = build('gmail', 'v1', credentials=creds)

    return service


# Searches the user's entire gmail account (not including spam) for emails matching the search term
def search_messages(service, user_id, search_term):
    all_ids = []

    try:
        total_number_emails = service.users().getProfile(userId=user_id).execute()["messagesTotal"]

        # Creates a list of all of the user's emails found matching the search term
        search_ids = service.users().messages().list(userId=user_id, q=search_term,
                                                     maxResults=total_number_emails).execute()

        num_results = search_ids["resultSizeEstimate"]

        if num_results == 0:
            print("There were 0 results found matching this search term.")
            return ""

        else:
            # While there is another page of emails matching the search id, loop through the current page and
            # then get the messages on the next page
            while "nextPageToken" in search_ids:
                message_ids = search_ids["messages"]
                for ids in message_ids:
                    all_ids.append(ids["id"])
                search_ids = service.users().messages().list(userId=user_id, q=search_term,
                                                             pageToken=search_ids["nextPageToken"],
                                                             maxResults=total_number_emails).execute()

            # If there is only one page of messages, get all of the message ids on that page
            if "nextPageToken" not in search_ids:
                message_ids = search_ids["messages"]
                for ids in message_ids:
                    all_ids.append(ids["id"])
            return all_ids

    except errors.HttpError as error:
        print(f"An error has occurred: {error}")


# If the label exists, the existing label id is returned, otherwise a new label is created and the new label's id is
# returned
def get_label_id(service, user_id, label_name):
    # Gets the existing labels that the user or system has created
    existing_labels = service.users().labels().list(userId=user_id).execute()["labels"]

    existing_label_info = {}

    # Adds the name and id of each existing label to a dictionary
    for label in existing_labels:
        existing_label_name = label["name"]
        existing_label_id = label["id"]
        existing_label_info.update({existing_label_name: existing_label_id})

    # If the label name matches the name of an existing label, return the label id, otherwise return None
    label_id = existing_label_info.get(label_name)

    # If the label does not exist, create a new label
    if label_id is None:
        body_dic = {"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
        new_label = service.users().labels().create(userId=user_id, body=body_dic).execute()
        label_id = new_label["id"]

    return label_id


# Labels the messages
def label_messages(service, user_id, search_term, label_name, remove_labels=False):
    try:
        add_ids = []
        remove_ids = []

        # Gets the label's id and adds it to a list of labels to add to the message
        label_id = get_label_id(service, user_id, label_name)
        add_ids.append(label_id)

        # If the user wants to Folder messages, the INBOX label will be added to the list of labels to remove
        if remove_labels:
            remove_ids.append("INBOX")

        # Gets all of the message ids matching the search term
        message_ids = search_messages(service, user_id, search_term)
        emails_labeled = len(message_ids)

        # Loops in increments of 1000 due to Gmail only allowing 1000 emails to be batch modified for every
        # call of batch modify. ids will take on the values of [0,1000,2000,3000,etc.]
        for ids in range(0, emails_labeled, 1000):
            # List slicing is used to get the message ids starting from the current value of ids to ids+1000,
            # so 0-1000, 1000-2000, 2000-3000, etc. A label is given and/or removed from each message based on the
            # message ids.
            service.users().messages().batchModify(userId=user_id,
                                                   body={"removeLabelIds": remove_ids,
                                                         "ids": message_ids[ids:ids + 1000],
                                                         "addLabelIds": add_ids}).execute()

        print(f"\n{emails_labeled} emails now have the label: {label_name}")

    except errors.HttpError as error:
        print(f"\nAn error has occurred: {error}")


# Deletes messages matching the search term
def delete_messages(service, user_id, search_term):
    message_ids = search_messages(service, user_id, search_term)
    emails_deleted = len(message_ids)

    for ids in range(0, emails_deleted, 1000):
        service.users().messages().batchDelete(userId=user_id, body={"ids": message_ids[ids:ids + 1000]}).execute()

    print(f"\n{emails_deleted} emails under the search term - {search_term} - have been deleted.")


# Puts everything together and asks for user input
def run_program():
    again = "yes"
    options = ["label", "delete", "folder"]

    email = str(input("Gmail email address: "))
    while not email:
        email = str(input("Please enter a gmail email address. "))

    while again.lower() == "yes":
        label_or_delete_or_folder = ""
        search_term = ""
        delete = ""
        label = ""

        search_term = str(input("\nSearch Term: "))
        while not search_term:
            search_term = str(input("Please enter a search term or all emails will be affected. "))

        print(f"\nYour Search Term: '{search_term}'")
        print(f"\nYou can either Label, Folder, or Delete the emails found under '{search_term}'")
        print("*Folder will label the email with a given label and remove it from your inbox*")
        while label_or_delete_or_folder.lower() not in options:
            label_or_delete_or_folder = str(input("Label, Folder, or Delete: "))

        if label_or_delete_or_folder.lower() == "label":
            label = str(input(f"\nLabel name: "))
            label_messages(get_service(), email, search_term, label, remove_labels=False)

        elif label_or_delete_or_folder.lower() == "folder":
            label = str(input(f"\n'Folder' name: "))
            label_messages(get_service(), email, search_term, label, remove_labels=True)

        elif label_or_delete_or_folder.lower() == "delete":
            delete = str(input(f"\nDelete all emails found under the search term - '{search_term}' (yes/no)? "))

            while delete.lower() != "yes" and delete.lower() != "no":
                delete = str(input(
                    f"Please answer yes or no to whether you would like to delete all of the emails under the search "
                    f"term: {search_term}? "))

            if delete.lower() == "yes":
                delete_messages(get_service(), email, search_term)
            elif delete.lower() == "no":
                print("\nDELETION CANCELLED!")

        again = ""
        while again.lower() != "yes" and again.lower() != "no":
            again = str(input("\nWould you like to continue sorting mail (yes/no): "))

    print("\nThank you for using THE BIG E Gmail Sorter! Have a nice day!")


run_program()
