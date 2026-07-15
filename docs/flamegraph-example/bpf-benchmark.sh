#!/bin/bash
# Generate flamegraphs for bpf-benchmark project
# This script demonstrates the iterative tagging workflow for agentpprof

set -e

AGENTPPROF="${AGENTPPROF:-agentpprof}"
PROJECT_ROOT="${PROJECT_ROOT:-$HOME/workspace/bpf-benchmark}"
OUTPUT_DIR="${OUTPUT_DIR:-$(dirname "$0")}"

# Tag rules developed through iterative refinement
TAG_RULES=(
  # Session rules
  --tag-rule 'session:paper=(?i)paper|arxiv|latex|论文'
  --tag-rule 'session:review=(?i)review|审核'
  --tag-rule 'session:cleanup=(?i)clean|docker|disk|空间'
  --tag-rule 'session:naming=(?i)kinsn|kprog|native|naming|名字'
  --tag-rule 'session:bench=(?i)native-sim|benchmark|tetr'

  # Prompt rules
  --tag-rule 'prompt:paper=(?i)paper|arxiv|latex|abstract|intro|section|写作|JIT|逻辑|翻译|主旨|TCB|kernel|benchmark|K2|Merlin|charact|atc|论文|开源|pdf|tex|段落|压缩|页'
  --tag-rule 'prompt:naming=(?i)kinsn|kprog|kfunc|kops|insn|NativeOps|名字|叫啥|换成|命名|datapath|application'
  --tag-rule 'prompt:review=(?i)review|审核|check|问题|diff|看看'
  --tag-rule 'prompt:git=(?i)commit|push|pull|git|submodule|patch|上游'
  --tag-rule 'prompt:cleanup=(?i)clean|ignore|docker|cache|disk|空间|REMOVING|磁盘|目录|用户|Volumes|Images|清理|GB'
  --tag-rule 'prompt:debug=(?i)fix|error|bug|broken|warning'
  --tag-rule 'prompt:subagent=(?i)subagent|task-notification'
  --tag-rule 'prompt:format=(?i)格式|字体|图|style|format|idiom|表格|table'
  --tag-rule 'prompt:edit=(?i)修|改|加|更新|减少|填|保持|不要|删|去掉|移除'
  --tag-rule 'prompt:author=(?i)author|yusheng|zhengjie|contributor|标注|Hao Sun|ETH'
  --tag-rule 'prompt:confirm=(?i)^嗯$|^是$|^好$|我看不到|你确定|确认|对$|ok$|yes$'
  --tag-rule 'prompt:context=(?i)session is being continued|Request interrupted'
  --tag-rule 'prompt:progress=(?i)进展|进度|如何了|完成|done'
  --tag-rule 'prompt:discuss=(?i)觉得|是不是|会不会|有没有|还是|呢$|想想|效果|什么|为什么|怎么|咋'
  --tag-rule 'prompt:continue=(?i)^继续$|讲解|分析一下|然后|接下来'
  --tag-rule 'prompt:chat=(?i)不不不|你先|bpf ext|谢谢|thanks'
  --tag-rule 'prompt:brainstorm=(?i)你觉得|你想想|你说一下|你分析|可能有|能不能|怎么写|是不是|我在想|我们的|一般|optimization|space|layer|变换|建议|方案'
  --tag-rule 'prompt:repo=(?i)submodule|github\.com|仓库|repo|Files mentioned|结论|文件|路径|目录'
  --tag-rule 'prompt:number=(?i)^\d+$|up to \d+|多少|几个|数字|\d+×'
  --tag-rule 'prompt:code=(?i)代码|函数|变量|参数|返回|调用|实现|struct|fn |def |class |ebpf|bpf|elf|compile|proof|sequence'
  --tag-rule 'prompt:query=(?i)还有吗|呢\?|吗\?$|是啥|什么意思|哪个|哪些|啥意思'
  --tag-rule 'prompt:table=(?i)│|┃|表|row|column|cell'
  --tag-rule 'prompt:tech=(?i)mechanically|enforce|oracle|memory|bulk|wasm|runtime|kernel|verifier|jit|llvm|native|cilium|xdp'
  --tag-rule 'prompt:plan=(?i)挑|选|报告|我就|只|先|算了|行了|可以了|收益|尽可能'
  --tag-rule 'prompt:ref=(?i)^main$|^master$|^HEAD$|branch|也有'
  --tag-rule 'prompt:perf=(?i)慢|快|速度|性能|per app|调|x86|跑'
  --tag-rule 'prompt:action=(?i)你来|允许|拿掉|不需要|resume|保留'
  --tag-rule 'prompt:compare=(?i)类似|一样|这里面|这样'
  --tag-rule 'prompt:ack=(?i)^(ok|好|嗯|是|对|yes|no|否|行|可以)$'

  # LLM response rules (match model output patterns)
  --tag-rule 'llm:paper=(?i)编译|tex|pdf|abstract|intro|section|段落|逻辑|翻译|论文'
  --tag-rule 'llm:git=(?i)commit|push|submodule|remote|branch|merge'
  --tag-rule 'llm:edit=(?i)修改|修复|继续|处理|让我|更新|添加|删除'
  --tag-rule 'llm:review=(?i)分析|检查|验证|问题|看|确认|发现'
  --tag-rule 'llm:naming=(?i)kinsn|kprog|kfunc|kops|insn|命名'
  --tag-rule 'llm:code=(?i)代码|函数|实现|返回|参数|调用|执行'
  --tag-rule 'llm:explain=(?i)解释|说明|意思|表示|理解|是指'
  --tag-rule 'llm:suggest=(?i)建议|可以|应该|需要|推荐|尝试'
  --tag-rule 'llm:confirm=(?i)好的|明白|了解|完成|已经|成功'
  --tag-rule 'llm:list=(?i)以下|如下|列表|步骤|方法'

)

echo "Generating flamegraphs for bpf-benchmark..."

for view in tokens files network time; do
  echo "  $view..."
  "$AGENTPPROF" \
    --project-root "$PROJECT_ROOT" \
    --project-name bpf-benchmark \
    "${TAG_RULES[@]}" \
    --view "$view" \
    -o "$OUTPUT_DIR/bpf-benchmark-${view}.svg"

  "$AGENTPPROF" \
    --project-root "$PROJECT_ROOT" \
    --project-name bpf-benchmark \
    "${TAG_RULES[@]}" \
    --view "$view" \
    -o "$OUTPUT_DIR/bpf-benchmark-${view}.folded"
done

echo "Done. Generated:"
ls -la "$OUTPUT_DIR"/bpf-benchmark-*.svg "$OUTPUT_DIR"/bpf-benchmark-*.folded 2>/dev/null || true
