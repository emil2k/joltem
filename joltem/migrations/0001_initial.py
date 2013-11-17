# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'User'
        db.create_table(u'joltem_user', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('gravatar_email', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('gravatar_hash', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('impact', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('completed', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('notifications', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'joltem', ['User'])

        # Adding model 'Notification'
        db.create_table(u'joltem_notification', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['joltem.User'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('json_kwargs', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('is_cleared', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('time_notified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('time_cleared', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('notifying_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('notifying_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('joltem', ['Notification'])

        # Adding model 'Vote'
        db.create_table(u'joltem_vote', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('voter_impact', self.gf('django.db.models.fields.BigIntegerField')()),
            ('is_accepted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('magnitude', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('time_voted', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('voter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['joltem.User'])),
            ('voteable_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('voteable_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('joltem', ['Vote'])

        # Adding model 'Comment'
        db.create_table(u'joltem_comment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('impact', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('acceptance', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('time_commented', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['joltem.User'])),
            ('commentable_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('commentable_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('joltem', ['Comment'])

        # Adding M2M table for field groups on 'User'
        m2m_table_name = db.shorten_name(u'joltem_user_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm[u'joltem.user'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['user_id', 'group_id'])

        # Adding M2M table for field user_permissions on 'User'
        m2m_table_name = db.shorten_name(u'joltem_user_user_permissions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm[u'joltem.user'], null=False)),
            ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
        ))
        db.create_unique(m2m_table_name, ['user_id', 'permission_id'])

        # Adding model 'Invite'
        db.create_table(u'joltem_invite', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('invite_code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('personal_note', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('is_contacted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_sent', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_clicked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_signed_up', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['joltem.User'], null=True, blank=True)),
            ('time_contacted', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('time_sent', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('time_clicked', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('time_signed_up', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('twitter', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('facebook', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('stackoverflow', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('github', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('personal_site', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal(u'joltem', ['Invite'])


    def backwards(self, orm):
        # Deleting model 'Notification'
        db.delete_table(u'joltem_notification')

        # Deleting model 'Vote'
        db.delete_table(u'joltem_vote')

        # Deleting model 'Comment'
        db.delete_table(u'joltem_comment')

        # Deleting model 'User'
        db.delete_table(u'joltem_user')

        # Removing M2M table for field groups on 'User'
        db.delete_table(db.shorten_name(u'joltem_user_groups'))

        # Removing M2M table for field user_permissions on 'User'
        db.delete_table(db.shorten_name(u'joltem_user_user_permissions'))

        # Deleting model 'Invite'
        db.delete_table(u'joltem_invite')


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
        'joltem.comment': {
            'Meta': {'object_name': 'Comment'},
            'acceptance': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'commentable_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'commentable_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'impact': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['joltem.User']"}),
            'time_commented': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        u'joltem.invite': {
            'Meta': {'object_name': 'Invite'},
            'email': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'facebook': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'github': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'is_clicked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_contacted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_sent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_signed_up': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'personal_note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'personal_site': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'stackoverflow': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'time_clicked': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'time_contacted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'time_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'time_signed_up': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'twitter': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['joltem.User']", 'null': 'True', 'blank': 'True'})
        },
        'joltem.notification': {
            'Meta': {'object_name': 'Notification'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_cleared': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'json_kwargs': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'notifying_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'notifying_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'time_cleared': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'time_notified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['joltem.User']"})
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
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'joltem.vote': {
            'Meta': {'object_name': 'Vote'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'magnitude': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time_voted': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'voteable_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'voteable_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'voter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['joltem.User']"}),
            'voter_impact': ('django.db.models.fields.BigIntegerField', [], {})
        },
        u'project.project': {
            'Meta': {'object_name': 'Project'},
            'admin_set': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['joltem.User']", 'symmetrical': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['joltem']
