<!--
  YamlEditor.vue - YAML 在线编辑器组件（基于 CodeMirror 6）
  
  文件功能说明：
    - 提供功能完善、高性能的 YAML 在线代码编辑器
    - 支持 YAML 语法高亮、One Dark 暗色主题
    - 内置行号显示、代码折叠、括号自动补全与匹配、矩形选择、光标高亮等核心功能
    - 支持撤销/重做、多光标编辑、搜索匹配高亮
    - 实现与 Vue v-model 双向绑定的平滑同步，避免光标跳动与循环触发
  
  Props 参数说明：
    - modelValue: String, 编辑器中的 YAML 文本内容（支持 v-model）
    - readonly: Boolean, 是否为只读模式（默认 false）
  
  Events 事件说明：
    - @update:modelValue: 编辑器内容改变时向父组件同步最新字符串
-->
<template>
  <div class="yaml-editor-container" ref="editorContainer"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'

// CodeMirror 6 核心模块导入
import { EditorState } from '@codemirror/state'
import {
  EditorView,
  keymap,
  lineNumbers,
  highlightActiveLineGutter,
  highlightSpecialChars,
  drawSelection,
  dropCursor,
  rectangularSelection,
  crosshairCursor,
  highlightActiveLine
} from '@codemirror/view'
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands'
import { searchKeymap, highlightSelectionMatches } from '@codemirror/search'
import { closeBrackets, closeBracketsKeymap } from '@codemirror/autocomplete'
import { foldGutter, foldKeymap, indentOnInput, bracketMatching } from '@codemirror/language'
import { yaml } from '@codemirror/lang-yaml'
import { oneDark } from '@codemirror/theme-one-dark'

// 组件入参定义
const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

// 事件派发定义
const emit = defineEmits(['update:modelValue'])

// DOM 容器与编辑器实例引用
const editorContainer = ref(null)
let view = null
let isUpdatingFromProps = false

/**
 * 构建 CodeMirror 6 的扩展集合
 * 包含基础编辑辅助、快捷键映射、语言语法解析、主题与监听器
 * 
 * @param {Function} onDocChange 文档变动时的回调函数
 * @returns {Array} CodeMirror 扩展数组
 */
const buildExtensions = (onDocChange) => {
  return [
    lineNumbers(),
    highlightActiveLineGutter(),
    highlightSpecialChars(),
    history(),
    foldGutter(),
    drawSelection(),
    dropCursor(),
    EditorState.allowMultipleSelections.of(true),
    indentOnInput(),
    bracketMatching(),
    closeBrackets(),
    rectangularSelection(),
    crosshairCursor(),
    highlightActiveLine(),
    highlightSelectionMatches(),
    keymap.of([
      ...closeBracketsKeymap,
      ...defaultKeymap,
      ...searchKeymap,
      ...historyKeymap,
      ...foldKeymap
    ]),
    yaml(),
    oneDark,
    EditorState.readOnly.of(props.readonly),
    EditorView.lineWrapping,
    EditorView.updateListener.of((update) => {
      if (update.docChanged && onDocChange) {
        onDocChange(update.state.doc.toString())
      }
    }),
    EditorView.theme({
      "&": { height: "100%", width: "100%" },
      ".cm-scroller": { overflow: "auto" }
    })
  ]
}

/**
 * 初始化并挂载 CodeMirror 编辑器实例
 */
const initEditor = () => {
  if (!editorContainer.value) return

  // 销毁旧实例（如果已存在）
  if (view) {
    view.destroy()
    view = null
  }

  // 文档更新回调：当用户在编辑器输入时通知外部 v-model
  const handleDocChange = (newContent) => {
    if (!isUpdatingFromProps) {
      emit('update:modelValue', newContent)
    }
  }

  // 创建编辑器状态与实例
  const state = EditorState.create({
    doc: props.modelValue ?? '',
    extensions: buildExtensions(handleDocChange)
  })

  view = new EditorView({
    state,
    parent: editorContainer.value
  })
}

// 监听外部 props.modelValue 变化，同步到编辑器
watch(
  () => props.modelValue,
  (newVal) => {
    if (view) {
      const currentDoc = view.state.doc.toString()
      const safeVal = newVal ?? ''
      if (safeVal !== currentDoc) {
        isUpdatingFromProps = true
        view.dispatch({
          changes: { from: 0, to: currentDoc.length, insert: safeVal }
        })
        isUpdatingFromProps = false
      }
    }
  }
)

// 监听只读属性变化
watch(
  () => props.readonly,
  () => {
    initEditor()
  }
)

onMounted(() => {
  nextTick(() => {
    initEditor()
  })
})

onBeforeUnmount(() => {
  if (view) {
    view.destroy()
    view = null
  }
})
</script>

<style scoped>
.yaml-editor-container {
  height: 100%;
  width: 100%;
  border: 1px solid var(--border-color, #333);
  border-radius: var(--radius-sm, 4px);
  overflow: hidden;
}

:deep(.cm-editor) {
  height: 100%;
}

:deep(.cm-scroller) {
  font-family: 'Fira Code', 'Consolas', 'Courier New', monospace;
  font-size: 14px;
}
</style>


