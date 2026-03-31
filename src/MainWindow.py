#!/usr/bin/env python3
import gi
import sys
import os
import subprocess
import base64
import pyotp
import pickle
import qrcode
from io import BytesIO
from gi.repository import GLib
import locale
from locale import gettext as _

APPNAME = "eta-otp-lock"
TRANSLATIONS_PATH = "/usr/share/locale"

locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)

import gui
gui._ = _

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GdkPixbuf

action_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "actions.py")


class MainWindow:
    def __init__(self, application):
        self.secret = self.generate_secret()

        gui.create_gui(self)
        self.application = application
        self.ui_window_main.set_application(application)

        self.ui_button_newotp.connect("clicked", self.on_newotp_event)
        self.ui_button_show.connect("clicked", self.on_show_event)
        self.ui_button_import.connect("clicked", self.on_import_event)
        self.ui_button_export.connect("clicked", self.on_export_event)
        self.ui_button_delete.connect("clicked", self.on_delete_event)
        self.ui_button_fromkey.connect("clicked", self.on_fromkey_event)
        self.ui_button_qr_back.connect("clicked", self.on_qr_back_event)
        self.ui_button_createuser.connect("clicked", self.on_createusers_event)
        self.ui_button_setpasswdusers.connect("clicked", self.on_setpasswdusers_event)
        self.ui_button_deluser.connect("clicked", self.on_delusers_event)
        self.ui_button_delogretmen.connect("clicked", self.on_delfixusers_event,"ogretmen")
        self.ui_button_delogrenci.connect("clicked", self.on_delfixusers_event,"ogrenci")

        self.ui_window_main.show_all()
        self.ui_button_qr_back.hide()
        self.ui_stack_main.set_visible_child_name("main")

        # Load global secret if exists
        sp = subprocess.run(["pkexec", action_file, "status"])
        if sp.returncode == 1:
            pass
        elif sp.returncode == 0:
            sp = subprocess.run(["pkexec", action_file, "load"], capture_output=True)
            self.secret = sp.stdout.decode("utf-8").strip()
            self.ui_stack_main.set_visible_child_name("settings")
        else:
            self.application.quit()

    ########### button events ###########

    def on_qr_back_event(self, widget):
        self.ui_button_qr_back.hide()
        self.ui_stack_main.set_visible_child_name("settings")
        
    def on_createusers_event(self, widget):
        GLib.idle_add(
                self.ui_label_status.set_text,
                _(f"Creating users. Please wait...")
            )
        self.info_dialog(_("Info"), _("Branch Accounts are being added. Please wait..."))
        users = [
			{"name": "turkce",  "fullname": "Türkçe"},
			{"name": "matematik",  "fullname": "Matematik"},
			{"name": "sosyal",  "fullname": "Sosyal Bil."},
			{"name": "fen",  "fullname": "Fen Bil."},
			{"name": "bilisim", "fullname": "Bilişim"},
			{"name": "gorsel",  "fullname": "Görsel Sanat"},
			{"name": "muzik",  "fullname": "Müzik"},
			{"name": "dikab", "fullname": "Din Kültürü"},
			{"name": "felsefe",  "fullname": "Felsefe Grubu"},
			{"name": "fizik",  "fullname": "Fizik"},
			{"name": "kimya",  "fullname": "Kimya"},
			{"name": "biyoloji",  "fullname": "Biyoloji"},
			{"name": "cografya",  "fullname": "Coğrafya"},
			{"name": "tarih",  "fullname": "Tarih"},								
			{"name": "turkdili",  "fullname": "Meslek Dersleri"},
			{"name": "meslek",  "fullname": "Felsefe Grubu"},
			{"name": "yabancidil", "fullname": "Yabancı Dil"}
        ]

        for user in users:
            username = user["name"]
            fullname = user["fullname"]
			# Kullanıcı oluştur
            cmd = [
				"sudo", "useradd",
				"-m", username,
				"-s", "/bin/bash",
				"-U",
				"-d", f"/home/{username}",
				"-c", fullname
            ]

            try:
                subprocess.run(cmd, check=True)
                print(f"Kullanıcı {username} ({fullname}) oluşturuldu.")
            except subprocess.CalledProcessError as e:
                print(f"Kullanıcı {username} oluşturulamadı: {e}")
        self.info_dialog(_("Info"), _("Branch Accounts Added..."))
            
    def on_setpasswdusers_event(self, widget):
        self.info_dialog(_("Info"), _("Branch Accounts passwords will be changed."))
        new_password = self.input_passwd(width=200, is_password=True)
        if not new_password:
            return

        users = [
            "turkce", "matematik", "sosyal", "fen",
            "bilisim", "gorsel", "muzik", "dikab","turkdili","felsefe",
            "fizik","kimya","biyoloji","tarih","cografya","meslek", "yabancidil"
        ]

        for username in users:
            cmd = ["sudo", "chpasswd"]

            try:
                subprocess.run(
                    cmd,
                    input=f"{username}:{new_password}",
                    text=True,
                    check=True
                )

                print(f"{username} parolası değişti")

            except subprocess.CalledProcessError as e:
                print(f"Hata: {e}")
        self.info_dialog(_("Info"), _("Branch Accounts passwords have been changed."))
        
    def on_delusers_event(self, widget):
        self.info_dialog(_("Info"), _("Branch Accounts are being deleted. Please wait..."))
        users = [
			{"name": "turkce",  "fullname": "Türkçe"},
			{"name": "matematik",  "fullname": "Matematik"},
			{"name": "sosyal", "fullname": "Sosyal Bil."},
			{"name": "fen",  "fullname": "Fen Bil."},
			{"name": "bilisim", "fullname": "Bilişim"},
			{"name": "gorsel", "fullname": "Görsel Sanat"},
			{"name": "muzik",  "fullname": "Müzik"},
			{"name": "dikab",  "fullname": "Din Kültürü"},
			{"name": "felsefe",  "fullname": "Felsefe Grubu"},
			{"name": "fizik",  "fullname": "Fizik"},
			{"name": "kimya",  "fullname": "Kimya"},
			{"name": "biyoloji",  "fullname": "Biyoloji"},
			{"name": "cografya",  "fullname": "Coğrafya"},
			{"name": "tarih",  "fullname": "Tarih"},								
			{"name": "turkdili",  "fullname": "Meslek Dersleri"},
			{"name": "meslek",  "fullname": "Felsefe Grubu"},
			{"name": "yabancidil",  "fullname": "Yabancı Dil"}
        ]

        for user in users:
            username = user["name"]
            cmd = ["sudo", "userdel", "-r", username]  # -r ev dizinini ve grubunu siler
            try:
                subprocess.run(cmd, check=True)
                print(f"Kullanıcı {username} silindi.")               
            except subprocess.CalledProcessError as e:
                print(f"Kullanıcı {username} silinemedi: {e}")				        
        self.info_dialog(_("Info"), _("Branch Accounts Deleted."))

    def on_delfixusers_event(self, widget, username):
        cmd = ["sudo", "userdel", "-r", username]

        try:
            subprocess.run(cmd, check=True)
            print(f"Kullanıcı {username} silindi.")
            self.info_dialog(_("Info"), _("User Deleted."))
        except subprocess.CalledProcessError as e:
            print(f"Kullanıcı {username} silinemedi: {e}")                


    def on_newotp_event(self, widget):
        self.secret = self.generate_secret()
        self.ui_stack_main.set_visible_child_name("settings")
        subprocess.run(["pkexec", action_file, "save", self.secret])

    def on_show_event(self, widget):
        self.update_qr()
        self.ui_stack_main.set_visible_child_name("qr")
        self.ui_button_qr_back.show()

    def on_delete_event(self, widget):
        self.ui_stack_main.set_visible_child_name("main")
        subprocess.run(["pkexec", action_file, "remove"])

    def on_fromkey_event(self, widget):
        secret = self.input_secret()
        if secret:
            if self.is_base32(secret):
                self.secret = secret
            else:
                self.secret = self.generate_secret(secret.encode("utf-8"))
            self.ui_stack_main.set_visible_child_name("settings")
            subprocess.run(["pkexec", action_file, "save", self.secret])

    def on_import_event(self, widget):
        filename = self.open_file()
        if filename:
            try:
                with open(filename, "rb") as f:
                    data = pickle.load(f)
                    self.secret = base64.b32encode(data["secret"]).decode("utf-8")
                self.ui_stack_main.set_visible_child_name("settings")
                subprocess.run(["pkexec", action_file, "save", self.secret])
            except:
                self.info_dialog("ERROR", _("Failed to read Pin file"))

    def on_export_event(self, widget):
        filename = self.save_file()
        if filename:
            try:
                with open(filename, "wb") as f:
                    data = {}
                    data["secret"] = base64.b32decode(self.secret.encode("utf-8"))
                    pickle.dump(data, file=f)
            except:
                self.info_dialog(_("Error"), _("Failed to export Pin key file"))

    ########### helper functions ###########

    def update_qr(self):
        self.ui_label_secret.set_text(self.secret)
        self.ui_image_qr.set_from_pixbuf(self.get_qr_code(self.secret))

    def generate_secret(self, random_bytes=None):
        if random_bytes is None:
            random_bytes = os.urandom(10)
        return base64.b32encode(random_bytes).decode("utf-8")

    def is_base32(self, data):
        if len(data) % 4 > 0:
            return False
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567="
        return all(c in alphabet for c in data)

    def get_qr_code(self, secret):
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri("GLOBAL@etap", issuer_name="pardus-etap")
        qr = qrcode.make(uri+"&algorithm=SHA1&digits=6&period=30", box_size=5)

        with BytesIO() as output:
            qr.save(output, format="PNG")
            output.seek(0)
            memory_stream = Gio.MemoryInputStream.new_from_data(output.getvalue(), None)
            return GdkPixbuf.Pixbuf.new_from_stream(memory_stream, None)

    ########### file pick / save ###########

    def open_file(self):
        dialog = Gtk.FileChooserDialog(
            title=_("Select a File"),
            parent=self.ui_window_main,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        filter = Gtk.FileFilter()
        filter.set_name(_("Pin keys"))
        filter.add_pattern("*.totp")
        dialog.add_filter(filter)

        filename = dialog.get_filename() if dialog.run() == Gtk.ResponseType.OK else None
        dialog.destroy()
        return filename

    def save_file(self):
        dialog = Gtk.FileChooserDialog(
            title=_("Save a File"),
            parent=self.ui_window_main,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)

        filter = Gtk.FileFilter()
        filter.set_name(_("Pin keys"))
        filter.add_pattern("*.totp")
        dialog.add_filter(filter)

        filename = None
        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            if not filename.endswith(".totp"):
                filename += ".totp"
        dialog.destroy()
        return filename

    ########### input / info dialogs ###########

    def input_secret(self):
        dialog = Gtk.Dialog(title=_("Enter a Secret"), parent=self.ui_window_main)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        dialog.get_content_area().add(box)

        entry = Gtk.Entry()
        entry.set_max_length(16)
        entry.set_placeholder_text(_("Enter your key here"))
        box.pack_start(entry, True, True, 0)

        dialog.show_all()
        user_input = entry.get_text() if dialog.run() == Gtk.ResponseType.OK else None
        dialog.destroy()
        return user_input

    def input_passwd(self, width=300, is_password=True):
        dialog = Gtk.Dialog(title=_("Enter a Passwd"), parent=self.ui_window_main)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        dialog.set_default_size(width + 100, 120)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(10)
        dialog.get_content_area().add(box)

        entry = Gtk.Entry()
        entry.set_max_length(32)
        entry.set_size_request(width, -1)

        # kontrol ediyoruz
        if is_password:
            entry.set_visibility(False)
            entry.set_invisible_char("*")
            entry.set_placeholder_text(_("Enter password"))
        else:
            entry.set_visibility(True)
            entry.set_placeholder_text(_("Enter text"))

        box.pack_start(entry, True, True, 0)

        dialog.show_all()

        response = dialog.run()
        user_input = entry.get_text() if response == Gtk.ResponseType.OK else None

        dialog.destroy()
        return user_input


    def info_dialog(self, msg, desc):
        dialog = Gtk.MessageDialog(
            parent=self.ui_window_main,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=msg
        )
        dialog.format_secondary_text(desc)
        dialog.run()
        dialog.destroy()
