<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409eff">
              <el-icon :size="30"><Microphone /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.total_recordings }}</div>
              <div class="stat-label">总录音数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67c23a">
              <el-icon :size="30"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.transcribed }}</div>
              <div class="stat-label">已转写</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e6a23c">
              <el-icon :size="30"><Star /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.scored }}</div>
              <div class="stat-label">已评分</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f56c6c">
              <el-icon :size="30"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.warnings }}</div>
              <div class="stat-label">风险预警</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>分数分布</span>
          </template>
          <div class="chart-container">
            <el-table :data="scoreTableData" style="width: 100%">
              <el-table-column prop="range" label="分数段" />
              <el-table-column prop="count" label="数量" />
              <el-table-column prop="percentage" label="占比">
                <template #default="{ row }">
                  {{ row.percentage }}%
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>坐席排名 (Top 10)</span>
          </template>
          <el-table :data="agentRankings" style="width: 100%">
            <el-table-column type="index" label="排名" width="60" />
            <el-table-column prop="agent_name" label="坐席" />
            <el-table-column prop="total_recordings" label="录音数" />
            <el-table-column prop="avg_score" label="平均分" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'

const overview = ref({
  total_recordings: 0,
  transcribed: 0,
  scored: 0,
  warnings: 0,
  avg_score: 0
})

const scoreDistribution = ref({})
const agentRankings = ref([])

const scoreTableData = computed(() => {
  const total = Object.values(scoreDistribution.value).reduce((a, b) => a + b, 0)
  const labels = {
    '0-60': '0-60分',
    '60-70': '60-70分',
    '70-80': '70-80分',
    '80-90': '80-90分',
    '90-100': '90-100分'
  }

  return Object.entries(scoreDistribution.value).map(([key, count]) => ({
    range: labels[key] || key,
    count,
    percentage: total > 0 ? ((count / total) * 100).toFixed(1) : 0
  }))
})

async function loadData() {
  try {
    const [overviewData, distData, rankingsData] = await Promise.all([
      api.statistics.overview({}),
      api.statistics.scoreDistribution({}),
      api.statistics.agentRankings({ limit: 10 })
    ])

    overview.value = overviewData
    scoreDistribution.value = distData
    agentRankings.value = rankingsData
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 5px;
}

.chart-container {
  height: 300px;
  overflow-y: auto;
}
</style>
