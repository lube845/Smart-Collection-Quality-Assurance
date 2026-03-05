<template>
  <div class="rule-detail">
    <el-page-header @back="goBack" content="规则详情" />

    <el-card style="margin-top: 20px" v-if="rule">
      <template #header>
        <div class="card-header">
          <span>{{ rule.name }} (v{{ rule.version }})</span>
          <el-tag :type="getStatusType(rule.status)">{{ getStatusText(rule.status) }}</el-tag>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="规则代码">{{ rule.code }}</el-descriptions-item>
        <el-descriptions-item label="及格分数">{{ rule.pass_score }}分</el-descriptions-item>
        <el-descriptions-item label="总分">{{ rule.total_score }}分</el-descriptions-item>
        <el-descriptions-item label="是否为最新">{{ rule.is_latest ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(rule.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="发布时间">{{ formatDate(rule.published_at) }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ rule.description || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>考核项列表</span>
          <el-button type="primary" size="small" @click="showItemDialog = true">
            <el-icon><Plus /></el-icon>
            添加考核项
          </el-button>
        </div>
      </template>
      <el-table :data="rule?.items || []" stripe>
        <el-table-column prop="name" label="考核项名称" />
        <el-table-column prop="code" label="代码" width="120" />
        <el-table-column prop="item_type" label="类型" width="100">
          <template #default="{ row }">
            {{ row.item_type === 'assessment' ? '考核项' : '信息确认' }}
          </template>
        </el-table-column>
        <el-table-column prop="max_score" label="满分" width="80" />
        <el-table-column prop="is_required" label="必检" width="60">
          <template #default="{ row }">
            {{ row.is_required ? '是' : '否' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_veto" label="一票否决" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_veto" type="danger">是</el-tag>
            <span v-else>否</span>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="100" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="editItem(row)">编辑</el-button>
            <el-button link type="danger" @click="deleteItem(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 考核项对话框 -->
    <el-dialog v-model="showItemDialog" :title="editItemId ? '编辑考核项' : '添加考核项'" width="600px">
      <el-form :model="itemForm" :rules="itemRules" ref="itemFormRef" label-width="100px">
        <el-form-item label="考核项名称" prop="name">
          <el-input v-model="itemForm.name" />
        </el-form-item>
        <el-form-item label="代码" prop="code">
          <el-input v-model="itemForm.code" />
        </el-form-item>
        <el-form-item label="类型" prop="item_type">
          <el-radio-group v-model="itemForm.item_type">
            <el-radio label="assessment">考核项</el-radio>
            <el-radio label="confirm">信息确认</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="满分" prop="max_score">
          <el-input-number v-model="itemForm.max_score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="是否扣分">
          <el-switch v-model="itemForm.is_deduction" />
        </el-form-item>
        <el-form-item label="必检">
          <el-switch v-model="itemForm.is_required" />
        </el-form-item>
        <el-form-item label="一票否决">
          <el-switch v-model="itemForm.is_veto" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="itemForm.category" placeholder="如: 开场规范、合规红线" />
        </el-form-item>
        <el-form-item label="匹配提示">
          <el-input v-model="itemForm.match_prompt" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showItemDialog = false">取消</el-button>
        <el-button type="primary" @click="handleItemSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import api from '@/api'

const route = useRoute()
const router = useRouter()

const rule = ref(null)
const showItemDialog = ref(false)
const editItemId = ref(null)
const submitting = ref(false)

const itemForm = reactive({
  name: '',
  code: '',
  item_type: 'assessment',
  max_score: 10,
  is_deduction: true,
  is_required: true,
  is_veto: false,
  category: '',
  match_prompt: ''
})

const itemRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入代码', trigger: 'blur' }],
  max_score: [{ required: true, message: '请输入满分', trigger: 'blur' }]
}

function goBack() {
  router.back()
}

function formatDate(date) {
  return date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '-'
}

function getStatusType(status) {
  const types = { draft: 'info', testing: 'warning', published: 'success', deprecated: 'danger' }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = { draft: '草稿', testing: '测试中', published: '已发布', deprecated: '已废弃' }
  return texts[status] || status
}

function editItem(item) {
  editItemId.value = item.id
  Object.assign(itemForm, {
    name: item.name,
    code: item.code,
    item_type: item.item_type,
    max_score: item.max_score,
    is_deduction: item.is_deduction,
    is_required: item.is_required,
    is_veto: item.is_veto,
    category: item.category,
    match_prompt: item.match_prompt
  })
  showItemDialog.value = true
}

async function deleteItem(item) {
  try {
    await ElMessageBox.confirm('确定要删除此考核项吗？', '警告', { type: 'warning' })
    await api.rule.deleteItem(item.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function handleItemSubmit() {
  submitting.value = true
  try {
    if (editItemId.value) {
      await api.rule.updateItem(editItemId.value, itemForm)
      ElMessage.success('更新成功')
    } else {
      await api.rule.createItem(rule.value.id, itemForm)
      ElMessage.success('添加成功')
    }
    showItemDialog.value = false
    loadData()
  } catch (e) {
    console.error(e)
  } finally {
    submitting.value = false
  }
}

async function loadData() {
  try {
    const res = await api.rule.get(route.params.id)
    rule.value = res
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
