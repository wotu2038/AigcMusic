#!/bin/bash
# AIGC任务监控脚本

echo "=========================================="
echo "AIGC任务实时监控"
echo "=========================================="
echo ""
echo "使用方法："
echo "  ./scripts/monitor_tasks.sh              # 查看最近任务"
echo "  ./scripts/monitor_tasks.sh --watch      # 实时监控"
echo "  ./scripts/monitor_tasks.sh --task-id 1  # 查看指定任务"
echo "  ./scripts/monitor_tasks.sh --processing # 查看处理中的任务"
echo ""

if [ "$1" == "--watch" ]; then
    echo "🔄 实时监控模式（每5秒刷新，按Ctrl+C退出）"
    echo ""
    while true; do
        docker exec aigcmusic-web python manage_task_monitor.py --mode processing
        echo ""
        echo "更新时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "----------------------------------------"
        sleep 5
    done
elif [ "$1" == "--task-id" ]; then
    docker exec aigcmusic-web python manage_task_monitor.py --task-id $2
elif [ "$1" == "--processing" ]; then
    docker exec aigcmusic-web python manage_task_monitor.py --mode processing
elif [ "$1" == "--failed" ]; then
    docker exec aigcmusic-web python manage_task_monitor.py --mode failed
else
    docker exec aigcmusic-web python manage_task_monitor.py --mode recent
fi

