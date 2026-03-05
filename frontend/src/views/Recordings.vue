<template>
  <div class="recordings-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>录音列表</span>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>
            上传录音
          </el-button>
        </div>
      </template>

      <!-- 搜索条件 -->
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="应用组">
          <el-select v-model="queryParams.app_group_id" placeholder="请选择" clearable>
            <el-option v-for="g in appGroups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="请选择" clearable>
            <el-option label="上传中" value="uploading" />
            <el-option label="已上传" value="uploaded" />
            <el-option label="转写中" value="transcribing" />
            <el-option label="已转写" value="transcribed" />
            <el-option label="评分中" value="scoring" />
            <el-option label="已评分" value="scored" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="queryParams.risk_level" placeholder="请选择" clearable>
            <el-option label="正常" value="normal" />
            <el-option label="警告" value="warning" />
            <el-option label="危险" value="danger" />
          </el-select>
        </el-form-item>
        <el-form-item label="坐席">
          <el-input v-model="queryParams.agent_id" placeholder="坐席工号" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="file_name" label="文件名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="agent_name" label="坐席" width="100" />
        <el-table-column prop="customer_phone" label="客户手机" width="120" />
        <el-table-column prop="call_time" label="通话时间" width="160">
          <template #default="{ row }">
            {{ row.call_time ? formatDate(row.call_time) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.risk_level === 'danger'" type="danger">危险</el-tag>
            <el-tag v-else-if="row.risk_level === 'warning'" type="warning">警告</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_score" label="总分" width="80">
          <template #default="{ row }">
            {{ row.total_score ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row.id)">查看</el-button>
            <el-button link type="primary" @click="playAudio(row)" :disabled="row.status !== 'uploaded' && row.status !== 'transcribed'">播放</el-button>
            <el-button link type="primary" @click="triggerScore(row)" :disabled="row.status !== 'transcribed'">评分</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
                  v-model:current-page="queryParams.page"
         <el-pagination
 v-model:page-size="queryParams.page_size"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @change="loadData"
        />
      </div>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传录音" width="500px">
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-width="100px">
        <el-form-item label="应用组" prop="app_group_id">
          <el-select v-model="uploadForm.app_group_id" placeholder="请选择">
            <el-option v-for="g in appGroups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="坐席工号" prop="agent_id">
          <el-input v-model="uploadForm.agent_id" placeholder="请输入坐席工号" />
        </el-form-item>
        <el-form-item label="坐席姓名" prop="agent_name">
          <el-input v-model="uploadForm.agent_name" placeholder="请输入坐席姓名" />
        </el-form-item>
        <el-form-item label="客户手机" prop="customer_phone">
          <el-input v-model="uploadForm.customer_phone" placeholder="请输入客户手机号" />
        </el-form-item>
        <el-form-item label="通话时间" prop="call_time">
          <el-date-picker v-model="uploadForm.call_time" type="datetime" placeholder="选择通话时间" />
        </el-form-item>
        <el-form-item label="录音文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            accept=".mp3,.wav,.amr"
          >
            <el-button>选择文件</el-button>
            <template #tip>
              <div class="upload-tip">支持 MP3/WAV/AMR 格式，单文件最大500MB</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import api from '@/api'

const router = useRouter()

const loading = ref(false)
const uploading = ref(false)
const list = ref([])
const total = ref(0)
const appGroups = ref([])
const showUploadDialog = ref(false)

const queryParams = reactive({
  app_group_id: null,
  status: null,
  risk_level: null,
  agent_id: '',
  page: 1,
  page_size: 20
})

const uploadForm = reactive({
  app_group_id: null,
  agent_id: '',
  agent_name: '',
  customer_phone: '',
  call_time: null,
  file: null,
  file_md5: '',
  file_size: 0,
  file_type: ''
})

const uploadRules = {
  app_group_id: [{ required: true, message: '请选择应用组', trigger: 'change' }]
}

async function loadData() {
  loading.value = true
  try {
    const res = await api.recording.list(queryParams)
    list.value = res.items
    total.value = res.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadAppGroups() {
  try {
    const res = await api.appGroup.list()
    appGroups.value = res
  } catch (e) {
    console.error(e)
  }
}

function resetQuery() {
  queryParams.app_group_id = null
  queryParams.status = null
  queryParams.risk_level = null
  queryParams.agent_id = ''
  queryParams.page = 1
  loadData()
}

function formatDate(date) {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

function getStatusType(status) {
  const types = {
    uploading: 'info',
    uploaded: 'success',
    transcribing: 'warning',
    transcribed: 'success',
    scoring: 'warning',
    scored: 'success',
    transcribe_failed: 'danger',
    score_failed: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    uploading: '上传中',
    uploaded: '已上传',
    transcribing: '转写中',
    transcribed: '已转写',
    scoring: '评分中',
    scored: '已评分',
    transcribe_failed: '转写失败',
    score_failed: '评分失败'
  }
  return texts[status] || status
}

function viewDetail(id) {
  router.push(`/recordings/${id}`)
}

async function playAudio(row) {
  try {
    const res = await api.recording.getPlayUrl(row.id)
    window.open(res.play_url, '_blank')
  } catch (e) {
    console.error(e)
  }
}

async function triggerScore(row) {
  try {
    await ElMessageBox.confirm('确定要触发评分吗？', '提示')
    await api.recording.triggerScore(row.id)
    ElMessage.success('评分任务已触发')
    loadData()
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

async function handleFileChange(file) {
  uploadForm.file = file.raw
  uploadForm.file_size = file.size
  uploadForm.file_type = file.name.split('.').pop()

  // 计算MD5
  const reader = new FileReader()
  reader.onload = (e) => {
    const buffer = e.target.result
    const wordArray = CryptoJS.lib.WordArray.create(buffer)
    uploadForm.file_md5 = CryptoJS.MD5(wordArray).toString()
  }
  reader.readAsArrayBuffer(file.raw)
}

async function handleUpload() {
  if (!uploadForm.file) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  try {
    // 初始化上传
    const initRes = await api.recording.initUpload({
      file_name: uploadForm.file.name,
      file_size: uploadForm.file_size,
      file_md5: uploadForm.file_md5,
      file_type: uploadForm.file_type,
      app_group_id: uploadForm.app_group_id,
      agent_id: uploadForm.agent_id,
      agent_name: uploadForm.agent_name,
      customer_phone: uploadForm.customer_phone,
      call_time: uploadForm.call_time
    })

    if (initRes.exists) {
      ElMessage.warning('文件已存在')
      return
    }

    // 上传文件
    await api.recording.upload(initRes.recording_id, uploadForm.file)

    ElMessage.success('上传成功')
    showUploadDialog.value = false
    loadData()
  } catch (e) {
    console.error(e)
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  loadData()
  loadAppGroups()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.upload-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}
</style>
