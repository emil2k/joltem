# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Project'
        db.delete_table(u'joltem_project')

        # Removing M2M table for field users on 'Project'
        db.delete_table('joltem_project_users')

        # Deleting model 'TaskBranch'
        db.delete_table(u'joltem_taskbranch')

        # Removing M2M table for field assignees on 'TaskBranch'
        db.delete_table('joltem_taskbranch_assignees')

        # Deleting model 'Task'
        db.delete_table(u'joltem_task')


    def backwards(self, orm):
        # Adding model 'Project'
        db.create_table(u'joltem_project', (
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'joltem', ['Project'])

        # Adding M2M table for field users on 'Project'
        db.create_table(u'joltem_project_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm[u'joltem.project'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'joltem_project_users', ['project_id', 'user_id'])

        # Adding model 'TaskBranch'
        db.create_table(u'joltem_taskbranch', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['joltem.Task'])),
        ))
        db.send_create_signal(u'joltem', ['TaskBranch'])

        # Adding M2M table for field assignees on 'TaskBranch'
        db.create_table(u'joltem_taskbranch_assignees', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('taskbranch', models.ForeignKey(orm[u'joltem.taskbranch'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'joltem_taskbranch_assignees', ['taskbranch_id', 'user_id'])

        # Adding model 'Task'
        db.create_table(u'joltem_task', (
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['joltem.Task'], null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['joltem.Project'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'joltem', ['Task'])


    models = {
        
    }

    complete_apps = ['joltem']