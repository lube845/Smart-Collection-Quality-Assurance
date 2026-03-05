<template>
  <div class="settings-page">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>组织管理</span>
          </template>
          <el-form :model="orgForm" label-width="100px">
            <el-form-item label="组织名称">
              <el-input v-model="orgForm.name" />
            </el-form-item>
            <el-form-item label="组织代码">
              <el-input v-model="orgForm.code" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="orgForm.description" type="textarea" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveOrg">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span>应用组管理</span>
          </template>
          <div class="app-group-list">
            <el-table :data="appGroups" stripe>
              <el-table-column prop="name" label="名称" />
              <el-table-column prop="code" label="代码" />
              <el-table-column prop="is_active" label="状态">
                <template #default="{ row }">
                  <el-tag :type="row.is_active ? 'success' : 'danger'">
                    {{ row.is_active ? '启用' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button link type="primary" @click="editAppGroup(row)">编辑</el-button>
                  <el-button link type="danger" @click="toggleAppGroup(row)">
                    {{ row.is_active ? '禁用' : '启用' }}
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-button type="primary" size="small" style="margin-top: 10px" @click="showAppGroupDialog = true">
            添加应用组
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>用户管理</span>
          </template>
          <el-table :data="users" stripe>
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="email" label="邮箱" />
            <el-table-column prop="full_name" label="姓名" />
            <el-table-column prop="role" label="角色">
              <template #default="{ row }">
                <el-tag>{{ getRoleText(row.role) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button link type="primary" @click="editUser(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 应用组对话框 -->
    <el-dialog v-model="showAppGroupDialog" title="应用组" width="400px">
      <el-form :model="appGroupForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="appGroupForm.name" />
        </el-form-item>
        <el-form-item label="代码">
          <el-input v-model="appGroupForm.code" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="appGroupForm.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAppGroupDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAppGroup">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const orgForm = reactive({
  name: '',
  code: '',
  description: ''
})

const appGroups = ref([])
const users = ref([])
const showAppGroupDialog = ref(false)
const appGroupForm = reactive({
  name: '',
  code: '',
  description: '',
  organization_id: 1
})

function getRoleText(role) {
  const texts = { super_admin: '超级管理员', org_admin: '组织管理员', user: '普通用户' }
  return texts[role] || role
}

async function saveOrg() {
  ElMessage.success('保存成功')
}

async function loadAppGroups() {
  try {
    const res = await api.appGroup.list()
    appGroups.value = res
  } catch (e) {
    console.error(e)
  }
}

function editAppGroup(row) {
  Object.assign(appGroupForm, row)
  showAppGroupDialog.value = true
}

async function toggleAppGroup(row) {
  try {
    await api.appGroup.update(row.id, { is_active: !row.is_active })
    ElMessage.success('更新成功')
    loadAppGroups()
  } catch (e) {
    console.error(e)
  }
}

async function saveAppGroup() {
  try {
    await api.appGroup.create(appGroupForm)
    ElMessage.success('创建成功')
    showAppGroupDialog.value = false
    loadAppGroups()
  } catch (e) {
    console.error(e)
  }
}

function editUser(row) {
  // TODO: 实现编辑用户
}

onMounted(() => {
  loadAppGroups()
})
</script>

<style scoped>
.app-group-list {
  max-height: 300px;
  overflow-y: auto;
}
</style>
