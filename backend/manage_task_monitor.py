#!/usr/bin/env python
"""
AIGC任务监控脚本
实时监控任务执行进度和状态
"""
import os
import sys
import django
import time
from datetime import datetime, timedelta

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.aigc.models import AIGCGenerationTask, AIGCContent
from django.utils import timezone


def format_duration(seconds):
    """格式化时长"""
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        return f"{int(seconds // 60)}分{int(seconds % 60)}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}小时{minutes}分钟"


def get_task_status_summary():
    """获取任务状态汇总"""
    total = AIGCGenerationTask.objects.count()
    pending = AIGCGenerationTask.objects.filter(status='pending').count()
    processing = AIGCGenerationTask.objects.filter(status='processing').count()
    completed = AIGCGenerationTask.objects.filter(status='completed').count()
    failed = AIGCGenerationTask.objects.filter(status='failed').count()
    
    return {
        'total': total,
        'pending': pending,
        'processing': processing,
        'completed': completed,
        'failed': failed
    }


def display_task_details(task):
    """显示任务详情"""
    print(f"\n{'='*80}")
    print(f"任务ID: {task.task_id}")
    print(f"任务类型: {task.get_task_type_display()}")
    print(f"歌曲: {task.song.title} - {task.song.artist}")
    print(f"状态: {task.get_status_display()}")
    print(f"操作人员: {task.operator.phone if task.operator else 'N/A'}")
    print(f"创建时间: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if task.completed_at:
        duration = (task.completed_at - task.created_at).total_seconds()
        print(f"完成时间: {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"执行时长: {format_duration(duration)}")
    elif task.status == 'processing':
        duration = (timezone.now() - task.created_at).total_seconds()
        print(f"已执行时长: {format_duration(duration)}")
    
    if task.error_message:
        print(f"错误信息: {task.error_message}")
    
    # 显示生成内容
    contents = AIGCContent.objects.filter(task=task)
    if contents.exists():
        print(f"\n生成内容 ({contents.count()} 条):")
        for content in contents:
            status_color = {
                'pending_review': '🟡',
                'approved': '🟢',
                'rejected': '🔴',
                'published': '🔵'
            }.get(content.status, '⚪')
            content_type_display = {
                'image': '图片',
                'text': '文字',
                'video': '视频',
                'audio': '音频'
            }.get(content.content_type, content.content_type)
            print(f"  {status_color} 内容ID: {content.content_id}, 类型: {content_type_display}, "
                  f"状态: {content.get_status_display()}")
            if content.content_type == 'image' and content.content_url:
                print(f"      URL: {content.content_url}")
            elif content.content_type == 'text' and content.content_text:
                preview = content.content_text[:50] + '...' if len(content.content_text) > 50 else content.content_text
                print(f"      预览: {preview}")
    else:
        print("\n生成内容: 暂无")


def monitor_tasks(mode='recent', task_id=None, watch=False):
    """监控任务"""
    print("\n" + "="*80)
    print("AIGC任务监控系统")
    print("="*80)
    
    # 显示状态汇总
    summary = get_task_status_summary()
    print(f"\n📊 任务状态汇总:")
    print(f"  总计: {summary['total']}")
    print(f"  ⏳ 待处理: {summary['pending']}")
    print(f"  🔄 处理中: {summary['processing']}")
    print(f"  ✅ 已完成: {summary['completed']}")
    print(f"  ❌ 失败: {summary['failed']}")
    
    if task_id:
        # 显示指定任务
        try:
            task = AIGCGenerationTask.objects.get(task_id=task_id)
            display_task_details(task)
        except AIGCGenerationTask.DoesNotExist:
            print(f"\n❌ 任务 {task_id} 不存在")
            return
    
    elif mode == 'recent':
        # 显示最近的任务
        print(f"\n📋 最近10个任务:")
        tasks = AIGCGenerationTask.objects.all().order_by('-created_at')[:10]
        if not tasks.exists():
            print("  暂无任务")
        else:
            for task in tasks:
                status_icon = {
                    'pending': '⏳',
                    'processing': '🔄',
                    'completed': '✅',
                    'failed': '❌'
                }.get(task.status, '⚪')
                
                print(f"\n  {status_icon} 任务 #{task.task_id} - {task.get_task_type_display()}")
                print(f"     歌曲: {task.song.title} - {task.song.artist}")
                print(f"     状态: {task.get_status_display()}")
                print(f"     创建时间: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if task.status == 'processing':
                    duration = (timezone.now() - task.created_at).total_seconds()
                    print(f"     已执行: {format_duration(duration)}")
    
    elif mode == 'processing':
        # 显示正在处理的任务
        print(f"\n🔄 正在处理的任务:")
        tasks = AIGCGenerationTask.objects.filter(status='processing').order_by('created_at')
        if not tasks.exists():
            print("  暂无正在处理的任务")
        else:
            for task in tasks:
                duration = (timezone.now() - task.created_at).total_seconds()
                print(f"\n  任务 #{task.task_id} - {task.get_task_type_display()}")
                print(f"     歌曲: {task.song.title}")
                print(f"     已执行: {format_duration(duration)}")
    
    elif mode == 'failed':
        # 显示失败的任务
        print(f"\n❌ 失败的任务:")
        tasks = AIGCGenerationTask.objects.filter(status='failed').order_by('-created_at')[:10]
        if not tasks.exists():
            print("  暂无失败的任务")
        else:
            for task in tasks:
                print(f"\n  任务 #{task.task_id} - {task.get_task_type_display()}")
                print(f"     歌曲: {task.song.title}")
                print(f"     错误: {task.error_message[:100] if task.error_message else 'N/A'}")
                print(f"     时间: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if watch:
        print("\n" + "="*80)
        print("实时监控模式 (按 Ctrl+C 退出)")
        print("="*80)
        try:
            while True:
                time.sleep(5)  # 每5秒刷新一次
                # 清屏（在某些终端可能不工作）
                print("\n" * 2)
                monitor_tasks(mode='processing')
                print(f"\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except KeyboardInterrupt:
            print("\n\n监控已停止")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AIGC任务监控工具')
    parser.add_argument('--mode', choices=['recent', 'processing', 'failed'], default='recent',
                       help='监控模式: recent(最近), processing(处理中), failed(失败)')
    parser.add_argument('--task-id', type=int, help='查看指定任务ID的详情')
    parser.add_argument('--watch', action='store_true', help='实时监控模式')
    
    args = parser.parse_args()
    
    monitor_tasks(mode=args.mode, task_id=args.task_id, watch=args.watch)

