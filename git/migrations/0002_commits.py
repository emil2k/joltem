# -*- coding: utf-8 -*-
from django.utils import timezone

from django.utils import timezone
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Branch'
        db.delete_table(u'git_branch')

        # Adding model 'Commit'
        db.create_table(u'git_commit', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sha', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('message_encoding', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('commit_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('repository', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['git.Repository'])),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('committer', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'git', ['Commit'])

        # Adding M2M table for field parents on 'Commit'
        db.create_table(u'git_commit_parents', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_commit', models.ForeignKey(orm[u'git.commit'], null=False)),
            ('to_commit', models.ForeignKey(orm[u'git.commit'], null=False))
        ))
        db.create_unique(u'git_commit_parents', ['from_commit_id', 'to_commit_id'])


    def backwards(self, orm):
        # Adding model 'Branch'
        db.create_table(u'git_branch', (
            ('repository', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['git.Repository'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reference', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('solution', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['solution.Solution'], null=True, blank=True)),
        ))
        db.send_create_signal(u'git', ['Branch'])

        # Deleting model 'Commit'
        db.delete_table(u'git_commit')

        # Removing M2M table for field parents on 'Commit'
        db.delete_table('git_commit_parents')


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
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'timezone.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'timezone.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'git.commit': {
            'Meta': {'object_name': 'Commit'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'commit_time': ('django.db.models.fields.DateTimeField', [], {}),
            'committer': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'message_encoding': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'parents_rel_+'", 'to': u"orm['git.Commit']"}),
            'repository': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['git.Repository']"}),
            'sha': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'})
        },
        u'git.repository': {
            'Meta': {'unique_together': "(('name', 'project'),)", 'object_name': 'Repository'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['project.Project']"})
        },
        u'project.project': {
            'Meta': {'object_name': 'Project'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'})
        }
    }

    complete_apps = ['git']