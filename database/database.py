#!/usr/local/bin/python3.4

"""
Database model
{
    "<sliceName>": {
        "status": "<status>"
        "fsm_name": "<fsm_name>"
    }
}

"""

from threading import Lock

class slice_database:
    """ Class to store references to all slices """

    def __init__(self):
        self.slice_db = dict()
        self.lock = Lock()

    def add_slice(self, status, name):
        """ Creates a new slice with the given name """
        self.lock.acquire()
        if name in self.slice_db:
            self.slice_db.pop(name)
        #    self.lock.release()
        #    raise ValueError("Error while adding slice \""+ name + "\": Already exists!")

        slice_entry = dict()
        slice_entry["status"] = status
        slice_entry["fsm_name"] = ""
        self.slice_db[name] = slice_entry
        self.lock.release()

    def del_slice(self, name):
        """ Deletes the slice with that name """
        self.lock.acquire()
        if not name in self.slice_db:
            self.lock.release()
            return
        #    raise ValueError("Error while deleting slice \""+ name + "\": Not exists!") 

        #del self.slice_db[name]
        self.slice_db.pop(name)
        self.lock.release()

    def update_status_slice(self, status, name):
        """ Updates the slice with that status for the given name """
        self.lock.acquire()
        if not name in self.slice_db:
            slice_entry = dict()
            slice_entry["status"] = status
            slice_entry["fsm_name"] = ""
            self.slice_db[name] = slice_entry
            self.lock.release()
            return
        #    raise ValueError("Error while updating slice \""+ name + "\": Not exists!") 

        self.slice_db[name]["status"] = status

        self.lock.release()

    def update_fsm_name_slice(self, fsm_name, name):
        """ Updates the slice with that fsm_name for the given name """
        self.lock.acquire()
        if not name in self.slice_db:
            slice_entry = dict()
            slice_entry["status"] = "CONFIGURED"
            slice_entry["fsm_name"] = fsm_name
            self.slice_db[name] = slice_entry
            self.lock.release()
            return
        #    raise ValueError("Error while updating slice \""+ name + "\": Not exists!") 

        self.slice_db[name]["status"] = status

        self.lock.release()

    def get_status_slice(self, name):
        """ Returns the status of slice """

        if not name in self.slice_db:
            return None
        #    raise ValueError("Error while geting status slice \""+ name + "\": Not exists!") 

        return self.slice_db[name]["status"]

    def get_fsm_name_slice(self, name):
        """ Returns the status of slice """

        if not name in self.slice_db:
            return None
        #    raise ValueError("Error while geting status slice \""+ name + "\": Not exists!") 

        return self.slice_db[name]["fsm_name"]

    def get_slice(self, name):
        """ Returns the slice (object) to perform operations in that slice """

        if not name in self.slice_db:
            return None
        #    raise ValueError("Error while geting slice \""+ name + "\": Not exists!") 

        return self.slice_db[name]

    def get_all_slices(self):
        """ Returns the slice database (object) to perform operations """

        return self.slice_db