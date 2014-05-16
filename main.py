#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#Packing List App Main

import os
import webapp2
import cgi
import jinja2
import validation
import listdetermination
from collections import namedtuple
from markupsafe import Markup, escape

from google.appengine.ext import db
from google.appengine.api import memcache

template_dir = os.path.join(os.path.dirname(__file__), 'packinglist') 
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),autoescape=True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

"""Registration"""
class Registration(Handler):
    def write_form(self, username="", error_user="", error_password="", error_verify="", 
        email="", error_email=""):
        self.render('registration.html', username=username, error_user=error_user, 
            error_password=error_password, error_verify=error_verify, 
            email=email, error_email=error_email)
    def get(self):
        self.write_form()
    def post(self):
        username, password = self.request.get("username"), self.request.get("password")
        verify, email = self.request.get("verify"), self.request.get("email")
        errors = validation.valid(username, password, verify, email)
        error_user, error_password, error_verify, error_email = "", "", "", ""
        #check if username already exists in googgledb
        b=db.GqlQuery("Select * from Users where username=:1", username)
        user = b.get()
        if user:
            error_user="Username already exists"
            username = ""
            self.write_form(username=username, error_user=error_user, email=email)
        else:
            if sum(errors)==0: #if there are no errors, redirect to success page
                global username
                #put username in cookie
                self.response.headers.add_header("set-cookie", "username=%s" %str(username))
                #store user info in database
                a = Users(username=username, password=password, email=email)
                a.put()
                self.response.headers.add_header("set-cookie", "username=%s" %str(username))    
                self.redirect("/packinglist/generator")

            else:
                error_user, error_password, error_verify, error_email = "", "", "", ""
                if errors[0]==1:
                    error_user="Invalid Username"
                if errors[1]==1:
                    error_password="Invalid Password"
                if errors[2]==1:
                    error_verify="Password Mismatch"
                if errors[3]==1:
                    error_email="Invalid Email"
                self.write_form(username, error_user, error_password, error_verify, email,
                error_email)

"""User login"""
class Login(Handler):
    def write_form(self, username="", error_login=""):
        self.render("login.html", username=username, error_login=error_login)
    def get(self):
        self.write_form()
    def post(self):
        username, password = self.request.get("username"), self.request.get("password")
        b=db.GqlQuery("Select * from Users where username=:1", username)
        user = b.get()
        if user and user.password==password:
            self.response.headers.add_header("set-cookie", "username=%s" %str(username))
            self.redirect("/packinglist/mytrips")
        elif user:
            error_login="Incorrect password"
            self.write_form(username=username, error_login=error_login)
        else:
            error_login="User doesn't exist"
            self.write_form(username="", error_login=error_login)

"""User dashboard"""
class MyTrips(Handler):
    def get(self):
        username=self.request.cookies.get("username")
        trips= db.GqlQuery("Select * from Preferences where username=:1 order by created desc", username)
        self.render("welcome.html", username=username, trips=trips)

"""User logout"""
class Logout(Handler):
    def get(self):
        self.response.headers.add_header("set-cookie", "username=;Path=/packinglist")
        self.redirect("/packinglist/login")

"""A form to fill in trip attributes"""
class Generator(Handler):
    def write_form(self, name="", days="", error_name="", error_days="", error_gender="", 
       error_temp="", welcome=""): #I need to make checkbox "sticky" too
        username=self.request.cookies.get("username")
        if username==None or username=="":
            welcome=""
        else:
            welcome=Markup("<b>Welcome, ")+username +Markup("</b><br>"
                "<a href='/packinglist/mytrips'>My trips</a><br>"
                "<a href='/packinglist/logout'>Not you? Logout</a>")
        self.render("generator.html", name=name, days=days, error_days=error_days, 
            error_gender=error_gender, error_temp=error_temp, welcome=welcome)
    def get(self):
        self.write_form()
    def post(self):
        name, days, gender = self.request.get("name"), self.request.get("days"), self.request.get("gender")
        cold, warm= self.request.get("cold"), self.request.get("warm")
        rainy, beach = self.request.get("rainy"), self.request.get("beach")
        work, hiking, festival = self.request.get("work"), self.request.get("hiking"), self.request.get("festival")
        style = self.request.get("style")
        username=self.request.cookies.get("username")
        error=0
        error_name, error_days, error_gender, error_temp = "", "", "", ""
        if name=="":
            error_name="Name is required"
            error=1
        if days=="" and not isinstance(days,int):
            error_days="Duration of trip is required, in whole numbers"
            error=1
        if gender=="":
            error_gender="Gender is required"
            error=1
        if all([cold=="", warm=="", rainy==""]):
            error_temp="Temperature is required"
            error=1
        if error==1:
            self.write_form(name=name, days=days, error_name=error_name, error_days=error_days, error_gender=error_gender,
                error_temp=error_temp)
        else:
            a = Preferences(name=name, days=int(days), gender=gender, cold=cold, warm=warm, rainy=rainy, beach=beach, 
                work=work, hiking=hiking, festival=festival, style=style, username=username)
            a.put()
            ident=str(a.key().id())
            p = db.GqlQuery("Select * from Packing")
            new=[]
            for e in p:
                status=listdetermination.status(gender=e.gender, type=e.type, 
                        gen_user=gender, beach=beach, hiking=hiking, festival=festival, 
                        work=work, cold=cold, rainy=rainy, weather=e.weather)
                quantity=listdetermination.quant(item=e.item, days=days, cold=cold, 
                        warm=warm, rainy=rainy, type_packer=style, freq=e.freq)
                def statement(item, quant):
                    if quantity != "":
                        return item + " ("+quantity+")"
                    else:
                        return item
                b = ListDatabase(item=e.item, gender=e.gender, freq=e.freq, weather=e.weather,
                    type=e.type, category=e.category, trip_name=name, 
                    status = status, quantity=quantity, ident=ident, 
                    statement=statement(e.item, quantity))
                new.append(b)
            db.put(new)
            self.redirect("/packinglist/checklist/%s" %str(ident))

"""Generating the checklist to an unique URL"""
class Checklist(Handler):
    def get(self, list_id):
        self.render_form(list_id=list_id)
    def render_form(self, name="", days="", cn="", tn="", 
        on="", cp="", tp="", op="", caterror="", entry="", list_id="", username=""):
        p=Preferences.get_by_id(long(list_id))
        ident=list_id #id of the trip
        username=self.request.cookies.get("username")
        cn = selector('Clothing', 'not packed', ident)
        tn = selector('Toiletry', 'not packed', ident)
        on = selector('Other', 'not packed', ident)
        cp = selector('Clothing', 'packed', ident)
        tp = selector('Toiletry', 'packed', ident)
        op = selector('Other', 'packed', ident)
        nplist=[cn, tn, on]
        packed, notpacked = [],[] #ids of the items
        for li in nplist:
            for e in li:
                notpacked.append(e.key().id())
        plist=[cp, tp, op]
        for li in plist:
            for e in li:
                packed.append(e.key().id())
        memcache.set("notpacked", notpacked)
        memcache.set("packed", packed)
        memcache.set("attributes", [ident, p.days, p.name])
        self.render("checklist.html", p=p, caterror=caterror, entry=entry, username=username,
            cn=cn, tn=tn, on=on, cp=cp, tp=tp, op=op)
        #I should use memcache on this after the first pull
    def post(self, list_id):
        ident=memcache.get("attributes")[0]
        name=memcache.get("attributes")[2]
        notpacked=memcache.get("notpacked") #how to set class member variables?
        packed=memcache.get("packed")
        updated=[]
        for e in notpacked:
            if self.request.get(str(e))=="on":
                p=db.GqlQuery("SELECT * "
                    "FROM ListDatabase "
                    "WHERE __key__=KEY('ListDatabase', :1) AND ident=:2", e, ident).get() #i think ident is redundant
                p.status="packed"
                updated.append(p)
        for e in packed:
            if self.request.get(str(e))=="on":
                p=db.GqlQuery("SELECT * "
                    "FROM ListDatabase "
                    "WHERE __key__=KEY('ListDatabase', :1) AND ident=:2", e, ident).get()
                p.status="not packed"
                updated.append(p)
        db.put(updated)      
        caterror=""
        entry=self.request.get("new")
        cat=self.request.get("cat")
        if entry!="" and cat=="":
            caterror="You need to select a category"
            self.render_form(name="", days="", cn="", tn="", on="", cp="", tp="", op="", 
                caterror=caterror, entry=entry, list_id=list_id) #"entry" does not output spaces after an error..
        else:
            if entry!="" and cat!="":
                b = ListDatabase(item=entry, statement=entry, category=cat, trip_name=name, 
                    ident=ident, status = "not packed", quantity="")
                b.put()
            self.redirect("/packinglist/checklist/%s#anchor" %str(ident))

def selector(category, status, ident):
    p = db.GqlQuery("SELECT * "
            "FROM ListDatabase "
            "WHERE category=:1 AND status=:2 AND ident=:3 "
            "ORDER BY item ASC",
            category, status, ident)
    return p

def itemidparse(url):
        init=url.find("checklist")+27
        item_id=url[init:init+16]
        return item_id, init

class Edit(Handler):
    def get(self, url, *a):
        url=self.request.url
        ident=memcache.get("attributes")[0]
        item_id, init = itemidparse(url)
        p=db.GqlQuery("Select * from ListDatabase "
            "where __key__=KEY('ListDatabase', :1) and ident =:2", long(item_id), ident).get()
        self.render("edit.html", p=p)
    def post(self, *a):
        url=self.request.url
        ident=memcache.get("attributes")[0]
        item_id, init = itemidparse(url)
        p=db.GqlQuery("Select * from ListDatabase "
            "where __key__=KEY('ListDatabase', :1) and ident =:2", long(item_id), ident).get()
        new = self.request.get("new")
        p.statement=new
        p.put()
        self.redirect(url[:init-1]+"#anchor")

class Remove(Handler):
    def get(self, url, *a):
        url=self.request.url
        ident=memcache.get("attributes")[0]
        item_id, init = itemidparse(url)
        p=db.GqlQuery("Select * from ListDatabase "
            "where __key__=KEY('ListDatabase', :1) and ident =:2", long(item_id), ident).get()
        p.delete()
        self.redirect(url[:init-1]+"#anchor")

"""Data tables"""
"""User Data"""
class Users(db.Model):
    username=db.StringProperty(required=True)
    password=db.TextProperty(required=True)
    email=db.StringProperty(required=False)
    created=db.DateTimeProperty(auto_now_add=True)

"""Collects all the trip attributes generated by the generator"""
class Preferences(db.Model):
    name=db.StringProperty(required=True)
    days=db.IntegerProperty(required=True)
    gender=db.StringProperty(required=True)
    username=db.StringProperty(required=False)
    cold=db.StringProperty(required=False)
    warm=db.StringProperty(required=False)
    rainy=db.StringProperty(required=False)
    beach=db.StringProperty(required=False)
    work=db.StringProperty(required=False)
    hiking=db.StringProperty(required=False)
    festival=db.StringProperty(required=False)
    style=db.StringProperty(required=False)
    created=db.DateTimeProperty(auto_now_add=True)

"""Database of item status by trip"""
class ListDatabase(db.Model):
    item=db.StringProperty(required=True)
    category=db.StringProperty(required=False)
    gender=db.StringProperty(required=False)
    freq = db.StringProperty(required=False)
    type = db.StringProperty(required = False)
    weather = db.StringProperty(required=False)
    status = db.StringProperty(required=False)
    quantity = db.StringProperty(required=False)
    trip_name = db.StringProperty(required=False)
    ident=db.StringProperty(required=False)
    statement=db.StringProperty(required=False)

"""Master database of the standard list items"""
class Packing(db.Model):
    item = db.StringProperty(required=True)
    gender = db.StringProperty(required=False)
    freq = db.StringProperty(required=False)
    type = db.StringProperty(required=False)
    weather = db.StringProperty(required=False)
    category = db.StringProperty(required=False)

"""Deletes all user and item data!!!"""
class MassDelete(Handler):
    def get(self):
        entries=db.GqlQuery("Select * from ListDatabase")
        for e in entries:
            e.delete()
        entries=db.GqlQuery("Select * from Preferences")
        for e in entries:
            e.delete()
        entries=db.GqlQuery("Select * from Users")
        for e in entries:
            e.delete()

"""Deletes all user and item data!!!"""
class DataDelete(Handler):
    def get(self):
        entries=db.GqlQuery("Select * from Packing")
        for e in entries:
            e.delete()
        entries=db.GqlQuery("Select * from Packing2")
        for e in entries:
            e.delete()
        entries=db.GqlQuery("Select * from Test2")
        for e in entries:
            e.delete()
        entries=db.GqlQuery("Select * from Test3")
        for e in entries:
            e.delete()

app = webapp2.WSGIApplication([
    ('/packinglist/signup', Registration),
    ('/packinglist/mytrips', MyTrips),
    ('/packinglist/login', Login),
    ('/packinglist/logout', Logout),
    ('/packinglist/generator', Generator),
    ('/packinglist/checklist/(\d+)', Checklist),
    ('/packinglist/checklist/(\d+)/(\d+)/edit', Edit),
    ('/packinglist/checklist/(\d+)/(\d+)/remove', Remove),
    ('/packinglist/massdelete', MassDelete),
    ('/packinglist/datadelete', DataDelete)
], debug=True)
