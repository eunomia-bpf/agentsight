#!/bin/bash
# Generate flamegraphs for agentsight project
# This script demonstrates the iterative tagging workflow for agentpprof

set -e

AGENTPPROF="${AGENTPPROF:-agentpprof}"
PROJECT_ROOT="${PROJECT_ROOT:-$HOME/workspace/agentsight}"
OUTPUT_DIR="${OUTPUT_DIR:-$(dirname "$0")}"

# Tag rules developed through iterative refinement
TAG_RULES=(
  # Session rules (match against session cwd/first prompt)
  --tag-rule 'session:release=(?i)release|publish|crates|version'
  --tag-rule 'session:review=(?i)review|审核|code review'
  --tag-rule 'session:debug=(?i)debug|fix|bug|error'
  --tag-rule 'session:docs=(?i)docs|readme|document'
  --tag-rule 'session:refactor=(?i)refactor|重构|cleanup'
  --tag-rule 'session:flame=(?i)flame|pprof|agentpprof'
  --tag-rule 'session:dev=(?i)agentsight|workspace'

  # Prompt rules - development activities
  --tag-rule 'prompt:review=(?i)review|审核|check|diff|pr|code review'
  --tag-rule 'prompt:debug=(?i)fix|error|bug|broken|warning|fail|为啥'
  --tag-rule 'prompt:git=(?i)commit|push|pull|git|merge|rebase|branch'
  --tag-rule 'prompt:test=(?i)test|cargo test|pytest|verify|运行'
  --tag-rule 'prompt:docs=(?i)docs|readme|document|说明|注释'
  --tag-rule 'prompt:refactor=(?i)refactor|重构|cleanup|整理'
  --tag-rule 'prompt:release=(?i)release|publish|version|发布'

  # Prompt rules - code activities
  --tag-rule 'prompt:code=(?i)代码|函数|变量|参数|返回|调用|实现|struct|fn |def |impl'
  --tag-rule 'prompt:edit=(?i)修|改|加|更新|减少|填|删|去掉|移除|换'
  --tag-rule 'prompt:create=(?i)创建|新建|添加|add|create|new'

  # Prompt rules - conversation
  --tag-rule 'prompt:confirm=(?i)^嗯$|^是$|^好$|^ok$|^yes$|对$|确认|按照你说的'
  --tag-rule 'prompt:query=(?i)吗\?$|是啥|什么意思|哪个|哪些|怎么|为什么|真的能|合理吗|回答什么|宽度是什么'
  --tag-rule 'prompt:discuss=(?i)觉得|想想|效果|建议|方案|考虑|是不是应该|应该|tag|分类'
  --tag-rule 'prompt:continue=(?i)^继续$|然后|接下来|下一步|重新生成'
  --tag-rule 'prompt:context=(?i)session is being continued|Request interrupted'
  --tag-rule 'prompt:subagent=(?i)subagent|task-notification|subagent 做'
  --tag-rule 'prompt:switch=(?i)切换|master|branch'
  --tag-rule 'prompt:inspect=(?i)看看|看一下|看下'
  --tag-rule 'prompt:view=(?i)视图|维度|排列|火焰图|llm call'
  --tag-rule 'prompt:file=(?i)/home/|\.rs|\.py|\.md|拆分|文件'
  --tag-rule 'prompt:parse=(?i)解析|session|estimate|kind|数据'
  --tag-rule 'prompt:design=(?i)别的|几种|分别|问题|有意义|设计|初衷'
  --tag-rule 'prompt:generate=(?i)生成|能不能|你能|对.*项目'
  --tag-rule 'prompt:check=(?i)还是旧的|有.*吗|unmatch'
  --tag-rule 'prompt:docs=(?i)Example|详细解释|一段话|论文|分析一下|逻辑|完整'
  --tag-rule 'prompt:web=(?i)localhost|http|serve|网站|网页|\.io|\.dev|demo|png|图'
  --tag-rule 'prompt:refer=(?i)参考|browser|url|request'

  # Prompt rules - project specific
  --tag-rule 'prompt:ebpf=(?i)ebpf|bpf|sslsniff|uprobe|tracepoint'
  --tag-rule 'prompt:flame=(?i)flame|pprof|profile|agentpprof'
  --tag-rule 'prompt:agent=(?i)agent|claude|codex|session'

  # Short prompts - match specific patterns, not catch-all
  --tag-rule 'prompt:ack=(?i)^(ok|好|嗯|是|对|yes|no|否)$'

  # LLM response rules - cover common patterns in model output
  # Order matters: more specific rules first, then general patterns
  --tag-rule 'llm:git=(?i)commit|push|merge|branch|rebase|git|版本'
  --tag-rule 'llm:test=(?i)测试|test|cargo test|pytest|运行测试|通过|失败'
  --tag-rule 'llm:file=(?i)文件|目录|路径|创建文件|读取|写入|保存'
  --tag-rule 'llm:code=(?i)代码|函数|实现|返回|参数|调用|执行|struct|impl|fn |def |变量|定义|类型'
  --tag-rule 'llm:edit=(?i)修改|修复|继续|处理|让我|更新|添加|删除|移除|替换|改为|改成'
  --tag-rule 'llm:review=(?i)分析|检查|验证|问题|看一下|确认|发现|检测|注意|审查'
  --tag-rule 'llm:explain=(?i)解释|说明|意思|表示|理解|是指|这是因为|因为|所以|原因'
  --tag-rule 'llm:suggest=(?i)建议|可以|应该|需要|推荐|尝试|使用|考虑'
  --tag-rule 'llm:confirm=(?i)好的|明白|了解|完成|已经|成功|没有问题|正确|好了'
  --tag-rule 'llm:list=(?i)以下|如下|列表|步骤|方法|首先|然后|接下来|最后|第一|第二'
  --tag-rule 'llm:action=(?i)执行|运行|启动|停止|安装|配置|设置'
  --tag-rule 'llm:result=(?i)结果|输出|返回值|得到|生成|产生'
  --tag-rule 'llm:state=(?i)状态|当前|目前|现在|之前|之后'
  --tag-rule 'llm:tool=(?i)工具|命令|脚本|程序'
  --tag-rule 'llm:query=(?i)你想|我来|请问|如果|怎么|为什么|什么|哪个'
  --tag-rule 'llm:english=(?i)^[A-Z][a-z].*\.$|^I |^The |^This |^Let me|^Now |^Here'
  # Tool use responses (when no text content, just tool calls)
  --tag-rule 'llm:tool=(?i)^tool: '
  # Token-only events (pure usage updates without content)
  --tag-rule 'llm:usage=(?i)^token report$'
)

echo "Generating flamegraphs for agentsight..."

for view in tokens files network time; do
  echo "  $view..."
  "$AGENTPPROF" \
    --project-root "$PROJECT_ROOT" \
    --project-name agentsight \
    "${TAG_RULES[@]}" \
    --view "$view" \
    -o "$OUTPUT_DIR/agentsight-${view}.svg"

  "$AGENTPPROF" \
    --project-root "$PROJECT_ROOT" \
    --project-name agentsight \
    "${TAG_RULES[@]}" \
    --view "$view" \
    -o "$OUTPUT_DIR/agentsight-${view}.folded"
done

echo "Done. Generated:"
ls -la "$OUTPUT_DIR"/agentsight-*.svg "$OUTPUT_DIR"/agentsight-*.folded 2>/dev/null || true
