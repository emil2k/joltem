# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Ratio'
        db.create_table(u'project_ratio', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('votes_in', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('votes_out', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('votes_ratio', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['project.Project'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='vote_ratio_set', to=orm['joltem.User'])),
        ))
        db.send_create_signal(u'project', ['Ratio'])

        # Adding unique constraint on 'Ratio', fields ['project', 'user']
        db.create_unique(u'project_ratio', ['project_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Ratio', fields ['project', 'user']
        db.delete_unique(u'project_ratio', ['project_id', 'user_id'])

        # Deleting model 'Ratio'
        db.delete_table(u'project_ratio')


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
        u'project.impact': {
            'Meta': {'unique_together': "(['project', 'user'],)", 'object_name': 'Impact'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'impact': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['project.Project']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'impact_set'", 'to': u"orm['joltem.User']"})
        },
        u'project.project': {
            'Meta': {'object_name': 'Project'},
            'admin_set': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'admin_project_set'", 'symmetrical': 'False', 'to': u"orm['joltem.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'developer_set': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'developer_project_set'", 'symmetrical': 'False', 'to': u"orm['joltem.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manager_set': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'manager_project_set'", 'symmetrical': 'False', 'to': u"orm['joltem.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'project.ratio': {
            'Meta': {'unique_together': "(['project', 'user'],)", 'object_name': 'Ratio'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['project.Project']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'vote_ratio_set'", 'to': u"orm['joltem.User']"}),
            'votes_in': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'votes_out': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'votes_ratio': ('django.db.models.fields.FloatField', [], {'null': 'True'})
        }
    }

    complete_apps = ['project']