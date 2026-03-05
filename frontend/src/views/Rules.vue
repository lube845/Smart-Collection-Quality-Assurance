<template>
  <div class="rules-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>评分规则</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            创建规则
          </el-button>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="name" label="规则名称" min-width="150" />
        <el-table-column prop="code" label="规则代码" width="120" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="pass_score" label="及格分" width="80" />
        <el-table-column prop="total_score" label="总分" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_latest" label="最新" width="60">
          <template #default="{ row }">
            <el-tag v-if="row.is_latest" type="success">是</el-tag>
            <span v-else>否</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row.id)">查看</el-button>
            <el-button link type="primary" @click="editRule(row)">编辑</el-button>
            <el-button link type="success" @click="publishRule(row)" :disabled="row.status === 'published'">发布</el-button>
            <el-button link type="danger" @click="deleteRule(row)" :disabled="row.status !== 'draft'">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showCreateDialog" :title="editId ? '编辑规则' : '创建规则'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="规则代码" prop="code">
          <el-input v-model="form.code" placeholder="请输入规则代码" :disabled="!!editId" />
        </el-form-item>
        <el-form-item label="版本号" prop="version">
          <el-input v-model="form.version" placeholder="如: v1.0.0" :disabled="!!editId" />
        </el-form-item>
        <el-form-item label="及格分数" prop="pass_score">
          <el-input-number v-model="form.pass_score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="总分" prop="total_score">
          <el-input-number v-model="form.total_score" :min="0" :max="200" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const list = ref([])
const showCreateDialog = ref(false)
const editId = ref(null)

const form = reactive({
  name: '',
  code: '',
  version: '',
  pass_score: 60,
  total_score: 100,
  description: '',
  organization_id: 1  // TODO: 动态获取
})

const rules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入规则代码', trigger: 'blur' }],
  version: [{ required: true, message: '请输入版本号', trigger: 'blur' }]
}

async function loadData() {
  loading.value = true
  try {
    const res = await api.rule.list()
    list.value = res
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function getStatusType(status) {
  const types = { draft: 'info', testing: 'warning', published: 'success', deprecated: 'danger' }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = { draft: '草稿', testing: '测试中', published: '已发布', deprecated: '已废弃' }
  return texts[status] || status
}

function viewDetail(id) {
  router.push(`/rules/${id}`)
}

function editRule(row) {
  editId.value = row.id
  Object.assign(form, {
    name: row.name,
    code: row.code,
    version: row.version,
    pass_score: row.pass_score,
    total_score: row.total_score,
    description: row.description
  })
  showCreateDialog.value = true
}

async function publishRule(row) {
  try {
    await ElMessageBox.confirm('确定要发布此规则吗？', '提示')
    await api.rule.publish(row.id)
    ElMessage.success('发布成功')
    loadData()
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

async function deleteRule(row) {
  try {
    await ElMessageBox.confirm('确定要删除此规则吗？', '警告', { type: 'warning' })
    await api.rule.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (editId.value) {
      await api.rule.update(editId.value, form)
      ElMessage.success('更新成功')
    } else {
      await api.rule.create(form)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    loadData()
  } catch (e) {
    console.error(e)
  } finally {
    submitting.value = false
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
