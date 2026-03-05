<template>
  <div class="recording-detail">
    <el-page-header @back="goBack" content="录音详情">
      <template #actions>
        <el-button type="primary" @click="playAudio" :disabled="!recording">
          <el-icon><VideoPlay /></el-icon>
          播放录音
        </el-button>
      </template>
    </el-page-header>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 左侧：录音信息 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>基本信息</span>
          </template>
          <el-descriptions :column="1" border v-if="recording">
            <el-descriptions-item label="文件名">{{ recording.file_name }}</el-descriptions-item>
            <el-descriptions-item label="坐席">{{ recording.agent_name }}</el-descriptions-item>
            <el-descriptions-item label="坐席工号">{{ recording.agent_id }}</el-descriptions-item>
            <el-descriptions-item label="客户手机">{{ recording.customer_phone }}</el-descriptions-item>
            <el-descriptions-item label="通话时间">{{ formatDate(recording.call_time) }}</el-descriptions-item>
            <el-descriptions-item label="时长">{{ recording.duration ? `${Math.floor(recording.duration)}秒` : '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(recording.status)">{{ getStatusText(recording.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="风险等级">
              <el-tag v-if="recording.risk_level === 'danger'" type="danger">危险</el-tag>
              <el-tag v-else-if="recording.risk_level === 'warning'" type="warning">警告</el-tag>
              <span v-else>正常</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 评分结果 -->
        <el-card style="margin-top: 20px" v-if="scoringResult">
          <template #header>
            <span>评分结果</span>
          </template>
          <div class="score-info">
            <div class="score-value" :class="{ passed: scoringResult.passed, rejected: scoringResult.is_rejected }">
              {{ scoringResult.total_score }}
            </div>
            <div class="score-label">总分 {{ scoringResult.is_rejected ? '(一票否决)' : '' }}</div>
          </div>
          <el-divider />
          <div class="result-status">
            <el-tag :type="scoringResult.passed ? 'success' : 'danger'" size="large">
              {{ scoringResult.passed ? '通过' : '未通过' }}
            </el-tag>
            <el-tag v-if="scoringResult.is_auto_scored" type="info" size="small">AI自动评分</el-tag>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：转写文本和评分明细 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>转写文本</span>
              <el-button link type="primary" @click="copyText">复制</el-button>
            </div>
          </template>
          <div class="transcript-container" v-if="recording?.transcript">
            <div
              v-for="(seg, index) in transcriptSegments"
              :key="index"
              class="transcript-segment"
              :class="{ 'agent': seg.speaker === 'agent', 'customer': seg.speaker === 'customer' }"
              @click="seekTo(seg.start_time)"
            >
              <div class="segment-speaker">
                {{ seg.speaker === 'agent' ? '坐席' : '客户' }}
                <span class="segment-time">{{ formatTime(seg.start_time) }}</span>
              </div>
              <div class="segment-text" :class="getSegmentClass(seg)">
                {{ seg.text }}
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无转写文本" />
        </el-card>

        <!-- 评分明细 -->
        <el-card style="margin-top: 20px" v-if="scoringResult">
          <template #header>
            <span>评分明细</span>
          </template>
          <el-table :data="scoringResult.details" stripe>
            <el-table-column prop="item_name" label="考核项" />
            <el-table-column prop="item_type" label="类型" width="80">
              <template #default="{ row }">
                {{ row.item_type === 'assessment' ? '考核项' : '信息确认' }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getDetailStatusType(row.status)">
                  {{ getDetailStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="得分" width="80">
              <template #default="{ row }">
                {{ row.score }}/{{ row.max_score }}
              </template>
            </el-table-column>
            <el-table-column prop="matched_text" label="匹配文本" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import api from '@/api'

const route = useRoute()
const router = useRouter()

const recording = ref(null)
const scoringResult = ref(null)

const transcriptSegments = computed(() => {
  if (!recording.value?.transcript_segments) return []
  return recording.value.transcript_segments
})

function goBack() {
  router.back()
}

function formatDate(date) {
  return date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '-'
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
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

function getDetailStatusType(status) {
  const types = { done: 'success', not_done: 'info', wrong: 'danger' }
  return types[status] || 'info'
}

function getDetailStatusText(status) {
  const texts = { done: '已做到', not_done: '未做到', wrong: '做错' }
  return texts[status] || status
}

function getSegmentClass(seg) {
  // 检查是否匹配到扣分项
  if (scoringResult.value?.details) {
    const matched = scoringResult.value.details.find(d =>
      d.matched_text && d.matched_text.includes(seg.text)
    )
    if (matched) {
      return matched.status === 'done' ? 'highlight-green' : 'highlight-red'
    }
  }
  return ''
}

function copyText() {
  const text = transcriptSegments.value.map(s => s.text).join('\n')
  navigator.clipboard.writeText(text)
  ElMessage.success('已复制到剪贴板')
}

function seekTo(time) {
  // TODO: 实现跳转到指定时间播放
  console.log('seek to', time)
}

async function playAudio() {
  try {
    const res = await api.recording.getPlayUrl(recording.value.id)
    window.open(res.play_url, '_blank')
  } catch (e) {
    console.error(e)
  }
}

async function loadData() {
  try {
    const id = route.params.id
    const [recData, scoreData] = await Promise.all([
      api.recording.get(id),
      api.recording.getScore(id)
    ])
    recording.value = recData
    scoringResult.value = scoreData?.scoring_result
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.recording-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score-info {
  text-align: center;
  padding: 20px;
}

.score-value {
  font-size: 48px;
  font-weight: bold;
  color: #67c23a;
}

.score-value.rejected {
  color: #f56c6c;
}

.score-label {
  color: #999;
  margin-top: 10px;
}

.result-status {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.transcript-container {
  max-height: 500px;
  overflow-y: auto;
}

.transcript-segment {
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.3s;
}

.transcript-segment:hover {
  background: #f5f7fa;
}

.transcript-segment.agent {
  background: #e6f7ff;
}

.transcript-segment.customer {
  background: #f6ffed;
}

.segment-speaker {
  font-size: 12px;
  color: #999;
  margin-bottom: 5px;
}

.segment-time {
  margin-left: 10px;
}

.segment-text {
  font-size: 14px;
  line-height: 1.6;
}

.highlight-red {
  background: #ffebeb;
  color: #f56c6c;
  padding: 2px 5px;
  border-radius: 3px;
}

.highlight-green {
  background: #f0f9eb;
  color: #67c23a;
  padding: 2px 5px;
  border-radius: 3px;
}
</style>
