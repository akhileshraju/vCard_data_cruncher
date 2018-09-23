import os
import vobject


class vCardDataCruncher:
    version_supported = [3.0]
    contact_categories_lookup = {'001': "only_name",
                                 '010': "only_email",
                                 '100': "only_tele",
                                 '101': "tele_and_name",
                                 '110': "tele_and_email",
                                 '011': "email_and_name",
                                 '111': "name_email_and_tele"}
    required_fields = {3.0: ["fn", "n"]}

    def __init__(self,
                 file_path: str):
        file_path = os.path.abspath(file_path)
        self.file_location = '/'.join(file_path.split('/')[:-1])
        self.file_name = file_path.split('/')[-1]
        self.contact_categories = dict()
        for _, entry in self.contact_categories_lookup.items():
            self.contact_categories[entry] = list()
        self.final_contacts_list = list()
        self.raw_contacts_list = list()
        self.raw_contacts_modified_atleast_once = False

        with open(f"{self.file_location}/{self.file_name}") as vcf_file:
            individual_contacts = []
            append_to_current_entry = False
            current_entry = ""
            for line in vcf_file:
                if line.startswith("BEGIN:VCARD"):
                    append_to_current_entry = True
                elif line.startswith("END:VCARD"):
                    current_entry += line
                    append_to_current_entry = False

                if append_to_current_entry:
                    current_entry += line
                else:
                    individual_contacts.append(current_entry)
                    current_entry = ""

            for contact in individual_contacts:
                v_contact = vobject.readOne(contact)
                self.raw_contacts_list.append(v_contact)
                # self.pretty_print(v_contact)

    @staticmethod
    def pretty_print(vcard_object: vobject.vCard()):
        print("\n---------------------------")
        for field in vcard_object.contents:
            field_contents = vcard_object.contents[field]
            for data in field_contents:
                print(f"{data.name}")
                print(f"\tValue - {data.value}")
        print("---------------------------")

    def sort_contacts_into_categories(self):
        for contact in self.intermediate_contacts_list:
            no_name = False
            no_tele = False
            no_email = False
            if 'fn' not in contact.contents or 'n' not in contact.contents:
                no_name = True
            if 'tel' not in contact.contents:
                no_tele = True
            if 'email' not in contact.contents:
                no_email = True
    
            category = f"{int(not no_tele)}{int(not no_email)}{int(not no_name)}"
            self.contact_categories[self.contact_categories_lookup[category]].append(contact)
    
    def merge_contacts_with_same_tele(self):
        print("\nMerging contacts with same telephone number")

        count = 0
        # Use this dict to keep a track of the number stored in the processed_list
        numbers_used = dict()
        if self.raw_contacts_modified_atleast_once:
            copy_of_latest_contacts_list = self.intermediate_contacts_list
        else:
            self.raw_contacts_modified_atleast_once = True
            copy_of_latest_contacts_list = self.raw_contacts_list

        processed_list = list()
        for contact in copy_of_latest_contacts_list:
            # Check if there is an entry for telephone numbers in the contact.
            if contact.contents.get('tel'):
                contact_number = contact.contents['tel'][0].value
                # If the number doesnt exists in the dict, then insert the contact into the processed list.
                if contact_number not in numbers_used:
                    processed_list.append(contact)
                    numbers_used[contact_number] = len(processed_list) - 1
                # Else, if there is a contact with the same number present,
                # copy those values from the current contact,
                # that are missing from the contact stored in the processed list.
                else:
                    count += 1
                    # print(f"Number {contact_number} already exists!")

                    # Get the contact from the processed_list that matches the current contact.
                    existing_entry_in_processed_list = processed_list[numbers_used[contact_number]]

                    # self.pretty_print(existing_entry_in_processed_list)

                    # If the current contact has email's that are not in the contact stored in the processed_list,
                    # add them to the contact stored.
                    if 'email' in contact.contents:
                        for email in contact.contents['email']:
                            if 'email' in existing_entry_in_processed_list.contents:
                                for email_stored in existing_entry_in_processed_list.contents['email']:
                                    if email_stored.value != email.value:
                                        existing_entry_in_processed_list.add('email').value = email.value
                            else:
                                existing_entry_in_processed_list.add('email').value = email.value

                    # If the current contact has tele's that are not in the contact stored in the processed_list,
                    # add them to the contact stored.
                    if 'tel' in contact.contents:
                        for tel in contact.contents['tel']:
                            if 'tel' in existing_entry_in_processed_list.contents:
                                for tel_stored in existing_entry_in_processed_list.contents['tel']:
                                    if tel_stored.value != tel.value:
                                        existing_entry_in_processed_list.add('tel').value = tel.value
                            else:
                                existing_entry_in_processed_list.add('tel').value = tel.value

                    # self.pretty_print(existing_entry_in_processed_list)

            # The contact doesn't have a phone number.
            # So just copy it and process it in some other function.
            else:
                processed_list.append(contact)

        print(f"\t#contacts before processing - {len(copy_of_latest_contacts_list)}")
        print(f"\t#contacts deleted - {count}")
        print(f"\t#contacts after processing - {len(processed_list)}")

        # Copy the contacts into the instance variable
        self.intermediate_contacts_list = processed_list

    def merge_contacts_with_same_fn(self):
        print("\nMerging contacts with same name")

        count = 0
        # Use this dict to keep a track of the number stored in the processed_list
        names_used = dict()
        if self.raw_contacts_modified_atleast_once:
            copy_of_latest_contacts_list = self.intermediate_contacts_list
        else:
            self.raw_contacts_modified_atleast_once = True
            copy_of_latest_contacts_list = self.raw_contacts_list

        processed_list = list()
        for contact in copy_of_latest_contacts_list:
            # Check if there is an entry for telephone numbers in the contact.
            if contact.contents.get('fn', None):
                contact_name = contact.contents['fn'][0].value
                if contact_name != "":
                    # If the number doesnt exists in the dict, then insert the contact into the processed list.
                    if contact_name not in names_used:
                        processed_list.append(contact)
                        names_used[contact_name] = len(processed_list) - 1
                        # Else, if there is a contact with the same number present,
                    # copy those values from the current contact,
                    # that are missing from the contact stored in the processed list.
                    else:
                        count += 1
                        # print(f"Contact named {contact_name} already exists!")

                        # Get the contact from the processed_list that matches the current contact.
                        existing_entry_in_processed_list = processed_list[names_used[contact_name]]

                        # self.pretty_print(existing_entry_in_processed_list)

                        # If the current contact has email's that are not in the contact stored in the processed_list,
                        # add them to the contact stored.
                        if 'email' in contact.contents:
                            for email in contact.contents['email']:
                                if 'email' in existing_entry_in_processed_list.contents:
                                    for email_stored in existing_entry_in_processed_list.contents['email']:
                                        if email_stored.value != email.value:
                                            existing_entry_in_processed_list.add('email').value = email.value
                                else:
                                    existing_entry_in_processed_list.add('email').value = email.value

                        # If the current contact has tele's that are not in the contact stored in the processed_list,
                        # add them to the contact stored.
                        if 'tel' in contact.contents:
                            for tel in contact.contents['tel']:
                                if 'tel' in existing_entry_in_processed_list.contents:
                                    for tel_stored in existing_entry_in_processed_list.contents['tel']:
                                        if tel_stored.value != tel.value:
                                            existing_entry_in_processed_list.add('tel').value = tel.value
                                else:
                                    existing_entry_in_processed_list.add('tel').value = tel.value

                        # self.pretty_print(existing_entry_in_processed_list)

                else:
                    processed_list.append(contact)

            # The contact doesn't have a name.
            # So just copy it and process it in some other function.
            else:
                processed_list.append(contact)

        print(f"\t#contacts before processing - {len(copy_of_latest_contacts_list)}")
        print(f"\t#contacts deleted - {count}")
        print(f"\t#contacts after processing - {len(processed_list)}")

        # Copy the contacts into the instance variable
        self.intermediate_contacts_list = processed_list

    def merge_contacts_with_same_email(self):
        print("\nMerging contacts with same email")

        count = 0
        # Use this dict to keep a track of the number stored in the processed_list
        emails_used = dict()
        if self.raw_contacts_modified_atleast_once:
            copy_of_latest_contacts_list = self.intermediate_contacts_list
        else:
            self.raw_contacts_modified_atleast_once = True
            copy_of_latest_contacts_list = self.raw_contacts_list

        processed_list = list()
        for contact in copy_of_latest_contacts_list:
            # Check if there is an entry for telephone numbers in the contact.
            if contact.contents.get('email', None):
                contact_email = contact.contents['email'][0].value
                # If the number doesnt exists in the dict, then insert the contact into the processed list.
                if contact_email not in emails_used:
                    processed_list.append(contact)
                    emails_used[contact_email] = len(processed_list) - 1

                # Else, if there is a contact with the same number present,
                # copy those values from the current contact,
                # that are missing from the contact stored in the processed list.
                else:
                    count += 1
                    # print(f"Contact with email {contact_email} already exists!")

                    # Get the contact from the processed_list that matches the current contact.
                    existing_entry_in_processed_list = processed_list[emails_used[contact_email]]

                    # self.pretty_print(existing_entry_in_processed_list)

                    # If the current contact has email's that are not in the contact stored in the processed_list,
                    # add them to the contact stored.
                    if 'email' in contact.contents:
                        for email in contact.contents['email']:
                            if 'email' in existing_entry_in_processed_list.contents:
                                for email_stored in existing_entry_in_processed_list.contents['email']:
                                    if email_stored.value != email.value:
                                        existing_entry_in_processed_list.add('email').value = email.value
                            else:
                                existing_entry_in_processed_list.add('email').value = email.value

                    # If the current contact has tele's that are not in the contact stored in the processed_list,
                    # add them to the contact stored.
                    if 'tel' in contact.contents:
                        for tel in contact.contents['tel']:
                            if 'tel' in existing_entry_in_processed_list.contents:
                                for tel_stored in existing_entry_in_processed_list.contents['tel']:
                                    if tel_stored.value != tel.value:
                                        existing_entry_in_processed_list.add('tel').value = tel.value
                            else:
                                existing_entry_in_processed_list.add('tel').value = tel.value

                    # self.pretty_print(existing_entry_in_processed_list)
            # The contact doesn't have an email.
            # So just copy it and process it in some other function.
            else:
                processed_list.append(contact)

        print(f"\t#contacts before processing - {len(copy_of_latest_contacts_list)}")
        print(f"\t#contacts deleted - {count}")
        print(f"\t#contacts after processing - {len(processed_list)}")

        # Copy the contacts into the instance variable
        self.intermediate_contacts_list = processed_list

    def interactively_filter_contacts(self):
        get_rid_of_all_contacts_with = dict()
        get_rid_of_all_contacts_with['only_email'] = True
        get_rid_of_all_contacts_with['only_name'] = True
        get_rid_of_all_contacts_with['only_tele'] = False
        get_rid_of_all_contacts_with['email_and_name'] = True

        write_without_asking_contacts_with = dict()
        write_without_asking_contacts_with['tele_and_name'] = True
        write_without_asking_contacts_with['name_email_and_tele'] = True

        for category in self.contact_categories:
            if not get_rid_of_all_contacts_with.get(category, False):
                if not write_without_asking_contacts_with.get(category, False):
                    for entry in self.contact_categories[category]:
                        self.pretty_print(entry)
                        choice = input("\nDo you want to get rid of this contact ? (Y/N): ")
                        if choice.upper() == 'N':
                            self.final_contacts_list.append(entry)
                else:
                    for entry in self.contact_categories[category]:
                        self.final_contacts_list.append(entry)

    def write_final_list_to_file(self):
        count = 0
        print(f"\n--> Processed file path - {self.file_location}/processed_{self.file_name}")
        with open(f"{self.file_location}/processed_{self.file_name}", 'w') as output_file:
            for entry in self.final_contacts_list:
                output_file.write(entry.serialize())
                count += 1
        print(f"--> Total number of contact - {count}")


if __name__ == '__main__':
    contacts_db1 = vCardDataCruncher("contacts.vcf")
    contacts_db1.merge_contacts_with_same_tele()
    contacts_db1.merge_contacts_with_same_fn()
    contacts_db1.merge_contacts_with_same_email()
    contacts_db1.sort_contacts_into_categories()
    contacts_db1.interactively_filter_contacts()
    contacts_db1.write_final_list_to_file()
    print()

