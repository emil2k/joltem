# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GitUploadPackEvent'
        db.create_table(u'gateway_gituploadpackevent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('time_posted', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('duration', self.gf('django.db.models.fields.BigIntegerField')()),
            ('bytes_in', self.gf('django.db.models.fields.BigIntegerField')()),
            ('bytes_out', self.gf('django.db.models.fields.BigIntegerField')()),
        ))
        db.send_create_signal(u'gateway', ['GitUploadPackEvent'])

        # Adding model 'GitReceivePackEvent'
        db.create_table(u'gateway_gitreceivepackevent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('time_posted', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('duration', self.gf('django.db.models.fields.BigIntegerField')()),
            ('bytes_in', self.gf('django.db.models.fields.BigIntegerField')()),
            ('bytes_out', self.gf('django.db.models.fields.BigIntegerField')()),
        ))
        db.send_create_signal(u'gateway', ['GitReceivePackEvent'])


    def backwards(self, orm):
        # Deleting model 'GitUploadPackEvent'
        db.delete_table(u'gateway_gituploadpackevent')

        # Deleting model 'GitReceivePackEvent'
        db.delete_table(u'gateway_gitreceivepackevent')


    models = {
        u'gateway.gitreceivepackevent': {
            'Meta': {'object_name': 'GitReceivePackEvent'},
            'bytes_in': ('django.db.models.fields.BigIntegerField', [], {}),
            'bytes_out': ('django.db.models.fields.BigIntegerField', [], {}),
            'duration': ('django.db.models.fields.BigIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time_posted': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        u'gateway.gituploadpackevent': {
            'Meta': {'object_name': 'GitUploadPackEvent'},
            'bytes_in': ('django.db.models.fields.BigIntegerField', [], {}),
            'bytes_out': ('django.db.models.fields.BigIntegerField', [], {}),
            'duration': ('django.db.models.fields.BigIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time_posted': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        }
    }

    complete_apps = ['gateway']