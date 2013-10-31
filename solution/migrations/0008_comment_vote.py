# -*- coding: utf-8 -*-
from django.utils import timezone

from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'VoteComment'
        db.delete_table(u'solution_votecomment')

        # Adding model 'CommentVote'
        db.create_table(u'solution_commentvote', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('voter_impact', self.gf('django.db.models.fields.BigIntegerField')()),
            ('vote', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('time_voted', self.gf('django.db.models.fields.DateTimeField')(default=timezone.now)),
            ('solution', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['solution.Solution'])),
            ('comment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['solution.Comment'])),
            ('voter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal(u'solution', ['CommentVote'])

        # Adding unique constraint on 'CommentVote', fields ['comment', 'voter']
        db.create_unique(u'solution_commentvote', ['comment_id', 'voter_id'])

        # Adding model 'Comment'
        db.create_table(u'solution_comment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('comment', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('time_commented', self.gf('django.db.models.fields.DateTimeField')(default=timezone.now)),
            ('solution', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['solution.Solution'])),
            ('commenter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal(u'solution', ['Comment'])


    def backwards(self, orm):
        # Removing unique constraint on 'CommentVote', fields ['comment', 'voter']
        db.delete_unique(u'solution_commentvote', ['comment_id', 'voter_id'])

        # Adding model 'VoteComment'
        db.create_table(u'solution_votecomment', (
            ('comment', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('time_commented', self.gf('django.db.models.fields.DateTimeField')(default=timezone.now)),
            ('commenter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('solution', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['solution.Solution'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'solution', ['VoteComment'])

        # Deleting model 'CommentVote'
        db.delete_table(u'solution_commentvote')

        # Deleting model 'Comment'
        db.delete_table(u'solution_comment')


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
        u'project.project': {
            'Meta': {'object_name': 'Project'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'})
        },
        u'solution.comment': {
            'Meta': {'object_name': 'Comment'},
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'commenter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'solution': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['solution.Solution']"}),
            'time_commented': ('django.db.models.fields.DateTimeField', [], {'default': 'timezone.now'})
        },
        u'solution.commentvote': {
            'Meta': {'unique_together': "(('comment', 'voter'),)", 'object_name': 'CommentVote'},
            'comment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['solution.Comment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'solution': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['solution.Solution']"}),
            'time_voted': ('django.db.models.fields.DateTimeField', [], {'default': 'timezone.now'}),
            'vote': ('django.db.models.fields.SmallIntegerField', [], {}),
            'voter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'voter_impact': ('django.db.models.fields.BigIntegerField', [], {})
        },
        u'solution.solution': {
            'Meta': {'object_name': 'Solution'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['project.Project']"}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['task.Task']"}),
            'time_accepted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'time_completed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'time_posted': ('django.db.models.fields.DateTimeField', [], {'default': 'timezone.now'}),
            'title': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'solution.vote': {
            'Meta': {'unique_together': "(('solution', 'voter'),)", 'object_name': 'Vote'},
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_rejected': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'solution': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['solution.Solution']"}),
            'time_voted': ('django.db.models.fields.DateTimeField', [], {'default': 'timezone.now'}),
            'vote': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'voter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'voter_impact': ('django.db.models.fields.BigIntegerField', [], {})
        },
        u'task.task': {
            'Meta': {'object_name': 'Task'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'tasks'", 'null': 'True', 'to': u"orm['solution.Solution']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['project.Project']"}),
            'time_closed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'time_posted': ('django.db.models.fields.DateTimeField', [], {'default': 'timezone.now'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['solution']