# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Authentication.project'
        db.add_column(u'git_authentication', 'project',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['project.Project'], null=True, blank=True),
                      keep_default=False)


        # Changing field 'Authentication.user'
        db.alter_column(u'git_authentication', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['joltem.User'], null=True))


    def backwards(self, orm):
        # Deleting field 'Authentication.project'
        db.delete_column(u'git_authentication', 'project_id')


        # User chose to not deal with backwards NULL issues for 'Authentication.user'
        raise RuntimeError("Cannot reverse this migration. 'Authentication.user' and its values cannot be restored.")

        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Authentication.user'
        db.alter_column(u'git_authentication', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['joltem.User']))

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'git.authentication': {
            'Meta': {'object_name': 'Authentication'},
            'fingerprint': ('django.db.models.fields.CharField', [], {'max_length': '47'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['project.Project']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['joltem.User']", 'null': 'True', 'blank': 'True'})
        },
        u'git.repository': {
            'Meta': {'object_name': 'Repository'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['project.Project']"}),
            'time_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'joltem.user': {
            'Meta': {'object_name': 'User'},
            'completed': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'gravatar_email': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'gravatar_hash': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'impact': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'notify_by_email': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'time_notified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'project.project': {
            'Meta': {'object_name': 'Project'},
            'admin_set': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'admin_project_set'", 'symmetrical': 'False', 'to': u"orm['joltem.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'developer_set': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'developer_project_set'", 'symmetrical': 'False', 'to': u"orm['joltem.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manager_set': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'manager_project_set'", 'symmetrical': 'False', 'to': u"orm['joltem.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'subscriber_set': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'subscriber_project_set'", 'symmetrical': 'False', 'to': u"orm['joltem.User']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['git']
