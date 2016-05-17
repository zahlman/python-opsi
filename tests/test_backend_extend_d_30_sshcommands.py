#!/usr/bin/env python
#-*- coding: utf-8 -*-

# This file is part of python-opsi.
# Copyright (C) 2013-2015 uib GmbH <info@uib.de>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Testing CRUD Methods for sshcommands (read from / write to jsonfile).

:author: Anna Sucher <a.sucher@uib.de>
:license: GNU Affero General Public License version 3
"""

from __future__ import absolute_import
from .Backends.File import FileBackendBackendManagerMixin
from .helpers import workInTemporaryDirectory, mock
import unittest, json
from contextlib import contextmanager
# import unittest, json


@contextmanager
def workWithEmptyCommandFile(backend):
     with workInTemporaryDirectory():
                filename = u'test_file.conf'
                with open(filename, "w"):
                        pass
                with mock.patch.object(backend, '_getSSHCommandFilename', return_value=filename):
                        yield

class SSHCommandsTestCase(unittest.TestCase, FileBackendBackendManagerMixin):
        """
        Testing the crud methods for json commands .
        """
        def setUp(self):
                self.setUpBackend()

                #self.filename=u'/home/sucher/tmp/json/com-test.json'
                # self.backend._deleteSshCommandFileContent()
                self.name1=u'UTestName1'
                self.menuText1=u'UTestMenu1'
                self.commands1=[]
                self.commands1.append(u'test 1')

                self.command1={u'id':self.name1, u'menuText':self.menuText1, u'commands':self.commands1}
                print("command1:")
                print(self.command1)

                self.name2=u'TUestName2'
                self.menuText2=u'UTestMenu2'
                self.commands2=[]
                self.commands2.append(u'test 2')
                self.command2={u'name':self.name2, u'menuText':self.menuText2, u'commands':self.commands2}

                self.name3=u'UTestName3'
                self.menuText3=u'UTestMenu3'
                self.commands3=[]
                self.commands3.append(u'test 3')
                self.command3={u'name':self.name3, u'menuText':self.menuText3, u'commands':self.commands3}
                # self.commands=[u'test1', u'test2']

                self.def_needSudo=False
                self.def_position=0
                self.def_tooltipText=u''
                self.def_parentMenuText=None
                # print(self.command1)
                # print(self.command2)
                # print(self.command3)


                self.def_command1={u'id':u'utestmenu1', u'menuText':self.menuText1, u'commands':self.commands1, u'needSudo':self.def_needSudo, u'position':self.def_position, u'tooltipText':self.def_tooltipText, u'parentMenuText':self.def_parentMenuText}
                self.def_commandlist1=[]
                self.def_commandlist1.append(self.def_command1)

                self.commandlist1=[]
                self.commandlist1.append(self.command1)

                self.commandlist11=[]
                self.commandlist11.append(self.command1)
                self.commandlist11.append(self.command1)

                self.commandlist2=[]
                self.commandlist2.append(self.command1)
                self.commandlist2.append(self.command2)

                self.commandlist3=[]
                self.commandlist3.append(self.command1)
                self.commandlist3.append(self.command2)
                self.commandlist3.append(self.command3)
                # self.backend.createCommands(self.commandlist3)

        def tearDown(self):
                self.tearDownBackend()
                # self.backend.deleteSSHCommands(self.name1,self.name2, self.name3)

        # def testReadCommand(self):

        #         print(self.backend.getSSHCommands())
        #         self.assertEqual(self.backend.getSSHCommands(), [], "readCommands is empty list (at beginning)")


        def testCreateCommand(self):
                with workWithEmptyCommandFile(self.backend._backend):
                        self.assertEqual(self.backend.getSSHCommands(), [], "readCommands is empty list (at beginning)")
                        print("Datei: {}".format(self.backend._backend._getSSHCommandFilename()))
                        # print("p1: {}".format(self.backend.createSSHCommands(self.commandlist1)))
                        return_command = self.backend.createSSHCommand( self.command1["menuText"], self.command1["commands"])
                        print("p1: {}".format(return_command))
                        print("p2: {}".format(self.def_commandlist1))
                        self.assertListEqual(return_command, self.def_commandlist1)
                        # self.assertEqual(self.backend.createSSHCommands(self.commandlist1) , self.def_commandlist1, "create command with strings")
                # self.assertListEqual(self.backend.createSSHCommand(self.command1["name"], self.command1["menuText"], self.command1["commands"]) , json.loads(self.commandlist1, "create command with strings"))
                # self.assertNotEquals(self.backend.createSSHCommand(self.command2["name"], self.command2["menuText"], self.commands2) , json.loads(self.commandlist1, "create the right command with strings"))

        # def testCreateCommands(self):
        #         self.assertEquals(self.backend.getSSHCommands(), [], "readCommands is empty list (at beginning)")
        #         self.assertEqual(self.backend.createSSHCommands(self.commandlist1) , self.commandlist1, "create single command as list")
        #         self.assertNotEquals(self.backend.createSSHCommands(self.commandlist2), self.commandlist1, "create the right single command as list ")
        #         self.assertListEqual(self.backend.createSSHCommands(self.commandlist11) , self.commandlist1, "do not create double commands (same names)")

        # def testUpdateCommand(self):
        #         self.assertEquals(self.backend.getSSHCommands(), [], "readCommands is empty list (at beginning)")
        #         self.u_name1=u'UTestName1'
        #         self.u_menuText1=u'UTestMenu1'
        #         self.u_menuText2=u'UTestMenu1Neu'
        #         self.u_command=[u'test']
        #         self.u_command1=[{u'name':self.u_name1, u'menuText':self.u_menuText1, u'commands':self.u_command}]
        #         self.u_command2=[{u'name':self.u_name1, u'menuText':self.u_menuText2, u'commands':self.u_command}]

        #         self.backend.createSSHCommand(self.u_name1, self.u_menuText1)
        #         self.assertListEqual(self.backend.updateSSHCommand(self.u_name1, self.u_menuText2), self.u_command2, "update command ")
        #         self.assertNotEquals(self.backend.updateSSHCommand(self.u_name1, self.u_menuText2), self.u_command1, "update right command")

        # def testDeleteCommand(self):
                # self.backend.createCommands(self.commandlist3)
                # self.assertEqual( self.backend.deleteCommand(self.command3["name"]) , self.commandlist2) #, "remove command")
                # self.assertEqual( self.backend.createCommands(self.commandlist3), self.backend.deleteCommand(self.command3["name"])) #, "remove command")


        # def testDeleteCommand(self):
        #         # self.backend.createCommand(name1, self.menuText, self.commands, self.needSudo, self.priority )
        #         # self.backend.createCommand(name2, self.menuText, self.commands, self.needSudo, self.priority )
        #         self.backend.createCommand(self.command1["name"], self.command1.["menuText"])
        #         self.backend.createCommand(self.command2["name"], self.command2.["menuText"])
        #         self.backend.createCommand(self.command3["name"], self.command3.["menuText"])
        #         self.backend.deleteCommand(self.command2["name"])
        #         commands=self.backend.readCommands()

        #         self.assertFalse(self.backend.getCommand(name1), commands)
        #         self.assertTrue(self.backend.getCommand(name2), commands)
        #         # self.assert()



if __name__ == '__main__':
    unittest.main()
