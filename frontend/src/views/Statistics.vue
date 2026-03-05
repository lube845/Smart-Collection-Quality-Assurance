<template>
  <div class="statistics-page">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>数据统计</span>
          </template>
          <el-form :inline="true" :model="queryParams">
            <el-form-item label="应用组">
              <el-select v-model="queryParams.app_group_id" placeholder="请选择" clearable>
                <el-option v-for="g in appGroups" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadData">查询</el-button>
              <el-button @click="handleExport">导出</el-button>
            </el-form-item>
          </el-form>
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
            <el-table :data="distributionData" style="width: 100%">
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
            <span>坐席排名</span>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const appGroups = ref([])
const dateRange = ref([])
const distributionData = ref([])
const agentRankings = ref([])

const queryParams = reactive({
  app_group_id: null,
  start_date: null,
  end_date: null
})

const labels = {
  '0-60': '0-60分',
  '60-70': '60-70分',
  '70-80': '70-80分',
  '80-90': '80-90分',
  '90-100': '90-100分'
}

async function loadAppGroups() {
  try {
    const res = await api.appGroup.list()
    appGroups.value = res
  } catch (e) {
    console.error(e)
  }
}

async function loadData() {
  queryParams.start_date = dateRange.value?.[0]
  queryParams.end_date = dateRange.value?.[1]

  try {
    const [distRes, rankRes] = await Promise.all([
      api.statistics.scoreDistribution(queryParams),
      api.statistics.agentRankings({ ...queryParams, limit: 20 })
    ])

    const total = Object.values(distRes).reduce((a, b) => a + b, 0)
    distributionData.value = Object.entries(distRes).map(([key, count]) => ({
      range: labels[key] || key,
      count,
      percentage: total > 0 ? ((count / total) * 100).toFixed(1) : 0
    }))

    agentRankings.value = rankRes
  } catch (e) {
    console.error(e)
  }
}

async function handleExport() {
  try {
    const response = await api.export.recordings(queryParams)
    // 创建下载链接
    const blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `录音统计_${new Date().toISOString().split('T')[0]}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadAppGroups()
  loadData()
})
</script>

<style scoped>
.chart-container {
  max-height: 400px;
  overflow-y: auto;
}
</style>
