#!/usr/bin/env python3
"""Republish remaining stuck resumes"""
import pika
import json
import sys
import os

def republish():
    """Republish stuck resumes to the queue"""
    
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv('RABBITMQ_HOST', 'rabbitmq'),
                port=5672,
                credentials=pika.PlainCredentials('guest', 'guest'),
                connection_attempts=3,
                retry_delay=2
            )
        )
        channel = connection.channel()
        print("✅ Connected to RabbitMQ")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    stuck_resumes = [
        ('39f41c54-3355-4670-812e-5ca26abcedee', 'priya_sharma_resume.pdf'),
        ('e0e46b56-0002-44e8-bba6-63e9f3053615', 'marcus_johnson_resume.pdf'),
        ('e4a36164-563a-4814-b3f2-15c1a483040f', 'aisha_patel_resume.pdf'),
        ('dc76bec1-b96d-475f-aaa4-064bcce9a087', 'david_chen_resume.pdf'),
        ('ba2dcdc7-d13b-4011-b72d-aca26b09395f', 'sofia_rodriguez_resume.pdf'),
        ('66cb764e-e687-446e-8be5-82d0d78291e9', 'priya_sharma_resume.pdf'),
        ('da5a9554-3bad-4cd2-94f8-780882732dbd', 'marcus_johnson_resume.pdf'),
        ('6c703ff0-7f5b-441f-9723-0a2295e356cd', 'aisha_patel_resume.pdf'),
        ('ebfb4958-2f12-4e2c-b9da-9f364dc66050', 'david_chen_resume.pdf'),
        ('67a24b5c-52ae-4340-8c7d-f9e793f429c0', 'sofia_rodriguez_resume.pdf'),
        ('e46414da-11e5-4546-8d8b-9ad651d5c0a3', 'priya_sharma_resume.pdf'),
        ('d74c969d-e946-4e93-84d3-a15fa6e98b2f', 'marcus_johnson_resume.pdf'),
        ('6d8a3391-d112-4a98-b1a9-823dd9fbdce2', 'aisha_patel_resume.pdf'),
        ('2ab1669e-be05-46d3-85b7-11e6291db6ce', 'david_chen_resume.pdf'),
        ('9b4e6d6a-a59d-4231-a4a4-a6271a33f698', 'sofia_rodriguez_resume.pdf'),
    ]
    
    try:
        count = 0
        for resume_id, filename in stuck_resumes:
            message = {
                'resume_id': resume_id,
                'file_path': f"/tmp/resumes/{resume_id}.pdf",
                'job_description': 'Looking for Python developer with ML experience and 5+ years experience'
            }
            
            channel.basic_publish(
                exchange='',
                routing_key='resume_queue',
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            count += 1
        
        print(f"✅ Republished {count} more resumes")
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    republish()
