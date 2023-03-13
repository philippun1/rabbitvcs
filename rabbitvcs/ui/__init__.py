#
# This is an extension to the Nautilus file manager to allow better
# integration with the Subversion source control system.
#
# Copyright (C) 2006-2008 by Jason Field <jason@jasonfield.com>
# Copyright (C) 2007-2008 by Bruce van der Kooij <brucevdkooij@gmail.com>
# Copyright (C) 2008-2010 by Adam Plumb <adamplumb@gmail.com>
#
# RabbitVCS is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# RabbitVCS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RabbitVCS;  If not, see <http://www.gnu.org/licenses/>.
#

"""

UI layer.

"""
from __future__ import absolute_import
import rabbitvcs.vcs.status
from rabbitvcs import APP_NAME, LOCALE_DIR, gettext

import os
from six.moves import range

from rabbitvcs.util import helper

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib

adwaita_available = True
try:
    gi.require_version("Adw", "1")
    from gi.repository import Adw
except Exception as e:
    adwaita_available = False

sa = helper.SanitizeArgv()
sa.restore()

_ = gettext.gettext


REVISION_OPT = (["-r", "--revision"], {"help": "specify the revision number"})
BASEDIR_OPT = (["-b", "--base-dir"], {})
QUIET_OPT = (
    ["-q", "--quiet"],
    {
        "help": "Run the add command quietly, with no UI.",
        "action": "store_true",
        "default": False,
    },
)
VCS_OPT = (["--vcs"], {"help": "specify the version control system"})

VCS_OPT_ERROR = _(
    "You must specify a version control system using the --vcs [svn|git] option"
)

#: Maps statuses to emblems.
STATUS_EMBLEMS = {
    rabbitvcs.vcs.status.status_normal: "rabbitvcs-normal",
    rabbitvcs.vcs.status.status_modified: "rabbitvcs-modified",
    rabbitvcs.vcs.status.status_added: "rabbitvcs-added",
    rabbitvcs.vcs.status.status_deleted: "rabbitvcs-deleted",
    rabbitvcs.vcs.status.status_ignored: "rabbitvcs-ignored",
    rabbitvcs.vcs.status.status_read_only: "rabbitvcs-locked",
    rabbitvcs.vcs.status.status_locked: "rabbitvcs-locked",
    rabbitvcs.vcs.status.status_unknown: "rabbitvcs-unknown",
    rabbitvcs.vcs.status.status_missing: "rabbitvcs-complicated",
    rabbitvcs.vcs.status.status_replaced: "rabbitvcs-modified",
    rabbitvcs.vcs.status.status_complicated: "rabbitvcs-complicated",
    rabbitvcs.vcs.status.status_calculating: "rabbitvcs-calculating",
    rabbitvcs.vcs.status.status_error: "rabbitvcs-error",
    rabbitvcs.vcs.status.status_unversioned: "rabbitvcs-unversioned",
}


class GtkTemplateHelper(object):
    gtktemplate_id = ""
    header = None
    button_box = None

    def __init__(self, gtktemplate_id = None):
        if gtktemplate_id:
            self.gtktemplate_id = gtktemplate_id

    def get_window(self, widget):
        if adwaita_available:
            window = Adw.ApplicationWindow()
            self.header = Adw.HeaderBar()
            box = Gtk.Box()
            box.set_orientation(Gtk.Orientation.VERTICAL)
            box.append(self.header)
            box.append(widget)
            window.set_content(box)
        else:
            window = Gtk.ApplicationWindow()
            box = Gtk.Box()
            box.set_orientation(Gtk.Orientation.VERTICAL)
            box.append(widget)
            window.set_child(box)

        window.set_title(self.gtktemplate_id)
        window.set_icon_name("rabbitvcs-small")

        return window
    
    def add_dialog_button(self, text, callback, suggested = False):
        button = Gtk.Button()
        button.set_label(text)
        button.connect("clicked", callback)
        if suggested:
            button.add_css_class("suggested-action")

        if adwaita_available:
            self.header.pack_start(button)
        else:
            if self.button_box == None:
                self.button_box = Gtk.Box()
                self.button_box.set_margin_start(6)
                self.button_box.set_margin_end(6)
                self.button_box.set_margin_bottom(6)
                self.button_box.set_spacing(6)
                self.button_box.set_hexpand(True)
                self.button_box.set_halign(Gtk.Align.END)
                box = self.window.get_child()
                box.append(self.button_box)

            self.button_box.append(button)

        return button


    def exec_dialog(self, parent, widget, on_response_callback = None):
        if adwaita_available:
            dialog = Adw.MessageDialog(transient_for = parent)
            dialog.set_heading(self.gtktemplate_id)
            dialog.set_extra_child(widget)
            dialog.add_response("ok", "Ok")
            dialog.add_response("cancel", "Cancel")
            dialog.connect("response", self.on_adw_dialog_response)
        else:
            dialog = Gtk.MessageDialog(transient_for = parent)
            dialog.set_title(self.gtktemplate_id)
            dialog.set_modal(True)
            dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Ok", Gtk.ResponseType.OK)
            dialog.connect("response", self.on_gtk_dialog_response)
            content = dialog.get_content_area()
            content.append(widget)

        self.on_response_callback = on_response_callback

        dialog.set_size_request(550, 0)
        dialog.show()
        
    def on_adw_dialog_response(self, dialog, response):
        if self.on_response != None:
            response_id = Gtk.ResponseType.CANCEL
            if response == "ok":
                response_id = Gtk.ResponseType.OK
            if self.on_response_callback:
                self.on_response_callback(response_id)
    
    def on_gtk_dialog_response(self, dialog, response_id):
        if self.on_response_callback:
            self.on_response_callback(response_id)

        dialog.destroy()

    def register_window(self):
        if adwaita_available:
            appl = Adw.Application.get_default()
        else:
            appl = Gtk.Application.get_default()
        
        appl.add_window(self.window)

    @staticmethod
    def run_application(on_activate):
        if adwaita_available:
            app = Adw.Application()
        else:
            app = Gtk.Application()

        app.connect('activate', on_activate)
        app.run()

    def on_cancel_clicked(self, widget):
        if self.window:
            self.window.close()

    def on_close_clicked(self, widget):
        if self.window:
            self.window.close()

class GtkBuilderWidgetWrapper(object):
    def __init__(self, gtkbuilder_filename=None, gtkbuilder_id=None, claim_domain=True):
        if gtkbuilder_filename:
            self.gtkbuilder_filename = gtkbuilder_filename

        if gtkbuilder_id:
            self.gtkbuilder_id = gtkbuilder_id

        self.claim_domain = claim_domain


class InterfaceView(GtkBuilderWidgetWrapper):
    """
    Every ui window should inherit this class and send it the "self"
    variable, the Gtkbuilder filename (without the extension), and the id of the
    main window widget.

    When calling from the __main__ area (i.e. a window is opened via CLI,
    call the register_gtk_quit method to make sure the main app quits when
    the app is destroyed or finished.

    """

    def __init__(self, *args, **kwargs):
        GtkBuilderWidgetWrapper.__init__(self, *args, **kwargs)
        self.do_gtk_quit = False

        # On OSX, there is a glitch where GTK applications do not always come to the front
        # when a launched (and methods like 'present()' don't appear to work correctly).
        # So until GTK on OSX is fixed let's work around this issue...
        import platform

        if platform.system() == "Darwin":
            try:
                import subprocess

                subprocess.Popen(
                    'osascript -e "tell application \\"Python\\" to activate"',
                    shell=True,
                )
            except:
                pass

    def hide(self):
        window = self.window
        if window:
            window.set_property("visible", False)

    def show(self):
        window = self.window
        if window:
            window.set_property("visible", True)

    def destroy(self):
        self.close()

    def close(self, threaded=False):
        window = self.window
        if window is not None:
            if threaded:
                helper.run_in_main_thread(window.destroy)
            else:
                window.destroy()

        if self.do_gtk_quit:
            Gtk.main_quit()

    def register_gtk_quit(self):
        window = self.window
        self.do_gtk_quit = True

        # This means we've already been closed
        if window is None:
            GLib.idle_add(Gtk.main_quit)

    def gtk_quit_is_set(self):
        return self.do_gtk_quit

    def on_destroy(self, widget):
        self.destroy()

    def on_cancel_clicked(self, widget):
        self.close()

    def on_close_clicked(self, widget):
        self.close()

    def on_refresh_clicked(self, widget):
        return True

    def on_key_pressed(self, widget, event, *args):
        if event.keyval == Gdk.keyval_from_name("Escape"):
            self.on_cancel_clicked(widget)
            return True

        if (
            event.state & Gdk.ModifierType.CONTROL_MASK
            and Gdk.keyval_name(event.keyval).lower() == "w"
        ):
            self.on_cancel_clicked(widget)
            return True

        if (
            event.state & Gdk.ModifierType.CONTROL_MASK
            and Gdk.keyval_name(event.keyval).lower() == "q"
        ):
            self.on_cancel_clicked(widget)
            return True

        if (
            event.state & Gdk.ModifierType.CONTROL_MASK
            and Gdk.keyval_name(event.keyval).lower() == "r"
        ):
            self.on_refresh_clicked(widget)
            return True

    def change_button(self, id, label=None, icon=None):
        """
        Replace label and/or icon of the named button.
        """

        button = self.get_widget(id)
        if label:
            button.set_label(label)
        if icon:
            image = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
            button.set_image(image)


class InterfaceNonView(object):
    """
    Provides a way for an interface to handle quitting, etc without having
    to have a visible interface.

    """

    def __init__(self):
        self.do_gtk_quit = False

    def close(self):
        if self.do_gtk_quit:
            if not Gtk.main_level():
                GLib.idle_add(Gtk.main_quit)
                self.do_gtk_quit = False
            else:
                try:
                    Gtk.main_quit()
                except RuntimeError:
                    raise SystemExit()

    def register_gtk_quit(self):
        self.do_gtk_quit = True

    def gtk_quit_is_set(self):
        return self.do_gtk_quit


class VCSNotSupportedError(Exception):
    """Indicates the desired VCS is not valid for a given action"""

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


def main(allowed_options=None, description=None, usage=None):
    from os import getcwd
    from sys import argv
    from optparse import OptionParser
    from rabbitvcs.util.helper import get_common_directory

    parser = OptionParser(usage=usage, description=description)

    if allowed_options:
        for (option_args, option_kwargs) in allowed_options:
            parser.add_option(*option_args, **option_kwargs)

    (options, args) = parser.parse_args(argv)

    # Convert "." to current working directory
    paths = args[1:]
    for i in range(0, len(paths)):
        if paths[i] == ".":
            paths[i] = getcwd()

    if not paths:
        paths = [getcwd()]

    if parser.has_option("--base-dir") and not options.base_dir:
        options.base_dir = get_common_directory(paths)

    return (options, paths)
