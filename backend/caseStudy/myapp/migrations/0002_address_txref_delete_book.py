# Generated by Django 4.2.4 on 2023-08-21 20:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=200)),
                ('total_received', models.PositiveBigIntegerField()),
                ('total_sent', models.PositiveBigIntegerField()),
                ('balance', models.BigIntegerField()),
                ('unconfirmed_balance', models.BigIntegerField()),
                ('final_balance', models.BigIntegerField()),
                ('n_tx', models.PositiveIntegerField()),
                ('unconfirmed_n_tx', models.PositiveIntegerField()),
                ('final_n_tx', models.PositiveIntegerField()),
                ('tx_url', models.URLField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TxRef',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tx_hash', models.CharField(max_length=255)),
                ('block_height', models.PositiveIntegerField()),
                ('tx_input_n', models.IntegerField()),
                ('tx_output_n', models.IntegerField()),
                ('value', models.BigIntegerField()),
                ('ref_balance', models.BigIntegerField()),
                ('confirmations', models.PositiveIntegerField()),
                ('confirmed', models.DateTimeField(blank=True, null=True)),
                ('double_spend', models.BooleanField(default=False)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='txrefs', to='myapp.address')),
            ],
        ),
        migrations.DeleteModel(
            name='Book',
        ),
    ]
