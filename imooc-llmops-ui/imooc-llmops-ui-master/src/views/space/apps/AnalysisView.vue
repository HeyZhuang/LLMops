<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import { GridComponent, TooltipComponent } from 'echarts/components'
import moment from 'moment'
import { useGetAppAnalysis, useGetTokenCostAnalysis } from '@/hooks/use-analysis'
import { useGetFeedbackStats } from '@/hooks/use-feedback'
import OverviewIndicator from '@/components/OverviewIndicator.vue'

use([GridComponent, LineChart, CanvasRenderer, TooltipComponent])

// 1.定义页面所需数据
const route = useRoute()
const { loading: getAppAnalysisLoading, app_analysis, loadAppAnalysis } = useGetAppAnalysis()
const { loading: getTokenCostLoading, token_cost, loadTokenCostAnalysis } = useGetTokenCostAnalysis()
const { loading: getFeedbackStatsLoading, feedback_stats, loadFeedbackStats } = useGetFeedbackStats()

// 2.计算趋势数据，让其符合ECharts的格式
const trendOption = computed(() => {
  const fields = [
    'total_messages_trend',
    'active_accounts_trend',
    'avg_of_conversation_messages_trend',
    'cost_consumption_trend',
  ]

  if (app_analysis.value) {
    return fields.reduce(
      (acc, field) => {
        acc[field] = {
          grid: { top: 20, bottom: 20, left: 30, right: 30 },
          tooltip: {
            trigger: 'item',
            axisPointer: { type: 'shadow' },
            backgroundColor: 'rgba(15,23,42,0.9)',
            borderColor: 'rgba(212,175,55,0.2)',
            textStyle: { color: '#F8F5F0' },
          },
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: app_analysis.value[field]?.x_axis?.map((value: number) => {
              return moment(value * 1000).format('MMM D, YYYY')
            }),
            splitLine: {
              show: true,
              lineStyle: { color: 'rgba(212,175,55,0.06)', width: 1, type: 'dashed' },
            },
            axisLine: { lineStyle: { color: 'rgba(212,175,55,0.15)' } },
            axisLabel: { color: '#7c87a2' },
          },
          yAxis: {
            type: 'value',
            splitLine: {
              lineStyle: { color: 'rgba(212,175,55,0.06)', type: 'dashed' },
            },
            axisLabel: { color: '#7c87a2' },
          },
          series: [
            {
              data: app_analysis.value?.[field]?.y_axis,
              type: 'line',
              smooth: true,
              lineStyle: { color: '#D4AF37', width: 2 },
              itemStyle: { color: '#D4AF37' },
              areaStyle: {
                color: {
                  type: 'linear',
                  x: 0, y: 0, x2: 0, y2: 1,
                  colorStops: [
                    { offset: 0, color: 'rgba(212,175,55,0.15)' },
                    { offset: 1, color: 'rgba(212,175,55,0)' },
                  ],
                },
              },
            },
          ],
        }
        return acc
      },
      {} as Record<string, any>,
    )
  }
  return fields.reduce(
    (acc, field) => {
      acc[field] = {}
      return acc
    },
    {} as Record<string, any>,
  )
})

onMounted(() => {
  const appId = String(route.params?.app_id)
  loadAppAnalysis(appId)
  loadTokenCostAnalysis(appId)
  loadFeedbackStats(appId)
})
</script>

<template>
  <div class="px-6 py-5 overflow-scroll scrollbar-w-none linen-bg">
    <!-- 概览指标 -->
    <div class="flex flex-col gap-5 mb-5">
      <!-- 标题 -->
      <div class="flex items-baseline gap-1">
        <div class="text-base text-abyss-800 font-semibold">概览指标</div>
        <div class="text-xs text-abyss-400">(过去7天)</div>
      </div>
      <!-- 指标卡片 -->
      <a-spin :loading="getAppAnalysisLoading">
        <div class="flex items-center gap-4">
          <overview-indicator
            title="全部会话数"
            help="反映 AI 每天的会话消息总数，在指定的时间范围内，用户对应用发起的请求总次数，一问一答记一次，用于衡量用户活跃度。"
            unit="次"
            :data="app_analysis?.total_messages?.data"
            :pop="app_analysis?.total_messages?.pop"
          >
            <template #icon>
              <icon-dashboard class="text-gold-400" />
            </template>
          </overview-indicator>
          <overview-indicator
            title="活跃用户数"
            help="指定的发布渠道和时间范围内，至少完成一轮对话的总使用用户数量，用于衡量应用吸引力。"
            unit="人"
            :data="app_analysis?.active_accounts?.data"
            :pop="app_analysis?.active_accounts?.pop"
          >
            <template #icon>
              <icon-computer class="text-gold-400" />
            </template>
          </overview-indicator>
          <overview-indicator
            title="平均会话互动数"
            help="反映每个会话用户的持续沟通次数，如果用户与 AI 进行了 10 轮对话，即为 10，该指标反映了用户粘性。"
            unit="次"
            :data="app_analysis?.avg_of_conversation_messages?.data"
            :pop="app_analysis?.avg_of_conversation_messages?.pop"
          >
            <template #icon>
              <icon-bulb class="text-gold-400" />
            </template>
          </overview-indicator>
          <overview-indicator
            title="Token输出速度"
            help="衡量 LLM 的性能，统计 LLM 从请求到输出完毕这段期间内的 Tokens 输出速度。"
            unit="Ts/秒"
            :data="app_analysis?.token_output_rate?.data"
            :pop="app_analysis?.token_output_rate?.pop"
          >
            <template #icon>
              <icon-language class="text-gold-400" />
            </template>
          </overview-indicator>
          <overview-indicator
            title="费用消耗"
            help="反映每日该应用请求语言模型的 Tokens 花费，用于成本控制。"
            unit="RMB"
            :data="app_analysis?.cost_consumption?.data"
            :pop="app_analysis?.cost_consumption?.pop"
          >
            <template #icon>
              <icon-code class="text-gold-400" />
            </template>
          </overview-indicator>
        </div>
      </a-spin>
    </div>
    <!-- 用户反馈统计 -->
    <div class="flex flex-col gap-5 mb-5">
      <div class="flex items-baseline gap-1">
        <div class="text-base text-abyss-800 font-semibold">用户反馈</div>
      </div>
      <a-spin :loading="getFeedbackStatsLoading">
        <div class="flex items-center gap-4">
          <div class="flex-1 glass metal-border rounded-xl p-5">
            <div class="text-abyss-400 text-sm mb-2">总反馈数</div>
            <div class="text-2xl text-abyss-800 font-bold">{{ feedback_stats?.total_count ?? 0 }}</div>
          </div>
          <div class="flex-1 glass metal-border rounded-xl p-5">
            <div class="text-abyss-400 text-sm mb-2">好评数</div>
            <div class="text-2xl text-gold-500 font-bold">{{ feedback_stats?.like_count ?? 0 }}</div>
          </div>
          <div class="flex-1 glass metal-border rounded-xl p-5">
            <div class="text-abyss-400 text-sm mb-2">差评数</div>
            <div class="text-2xl text-red-400 font-bold">{{ feedback_stats?.dislike_count ?? 0 }}</div>
          </div>
          <div class="flex-1 glass metal-border rounded-xl p-5">
            <div class="text-abyss-400 text-sm mb-2">满意度</div>
            <div class="text-2xl text-abyss-800 font-bold">
              {{ ((feedback_stats?.satisfaction_rate ?? 0) * 100).toFixed(1) }}%
            </div>
          </div>
        </div>
      </a-spin>
    </div>
    <!-- Token成本分析 -->
    <div class="flex flex-col gap-5 mb-5">
      <div class="flex items-baseline gap-1">
        <div class="text-base text-abyss-800 font-semibold">Token成本分析</div>
        <div class="text-xs text-abyss-400">(过去7天)</div>
      </div>
      <a-spin :loading="getTokenCostLoading">
        <div class="flex items-center gap-4 mb-4">
          <div class="flex-1 glass metal-border rounded-xl p-5">
            <div class="text-abyss-400 text-sm mb-2">总Token消耗</div>
            <div class="text-2xl text-abyss-800 font-bold">{{ token_cost?.total_token_count ?? 0 }}</div>
          </div>
          <div class="flex-1 glass metal-border rounded-xl p-5">
            <div class="text-abyss-400 text-sm mb-2">总费用 (RMB)</div>
            <div class="text-2xl text-gold-500 font-bold">{{ (token_cost?.total_cost ?? 0).toFixed(4) }}</div>
          </div>
          <div class="flex-1 glass metal-border rounded-xl p-5">
            <div class="text-abyss-400 text-sm mb-2">平均每次Token</div>
            <div class="text-2xl text-abyss-800 font-bold">{{ (token_cost?.avg_token_per_message ?? 0).toFixed(0) }}</div>
          </div>
        </div>
      </a-spin>
    </div>
    <!-- 指标详情 -->
    <div class="flex flex-col gap-5">
      <!-- 标题 -->
      <div class="flex items-baseline gap-1">
        <div class="text-base text-abyss-800 font-semibold">详细指标</div>
        <div class="text-xs text-abyss-400">(过去7天)</div>
      </div>
      <!-- 可视化图表 -->
      <a-spin :loading="getAppAnalysisLoading">
        <div class="grid grid-cols-2 gap-4">
          <div class="flex flex-col glass metal-border rounded-xl p-5 h-[300px]">
            <div class="flex items-center gap-2 mb-1 flex-shrink-0">
              <div class="text-abyss-800 font-bold">全部会话数</div>
              <a-tooltip content="反映 AI 每天的会话消息总数，在指定的时间范围内，用户对应用发起的请求总次数，一问一答记一次，用于衡量用户活跃度。">
                <icon-question-circle-fill class="text-gold-300" />
              </a-tooltip>
            </div>
            <div class="text-abyss-400 text-sm mb-1 flex-shrink-0">过去7天</div>
            <div class="w-full flex-1">
              <v-chart :init-options="{}" :option="trendOption?.total_messages_trend" :autoresize="true" />
            </div>
          </div>
          <div class="flex flex-col glass metal-border rounded-xl p-5 h-[300px]">
            <div class="flex items-center gap-2 mb-1 flex-shrink-0">
              <div class="text-abyss-800 font-bold">活跃用户数</div>
              <a-tooltip content="指定的发布渠道和时间范围内，至少完成一轮对话的总使用用户数量，用于衡量应用吸引力。">
                <icon-question-circle-fill class="text-gold-300" />
              </a-tooltip>
            </div>
            <div class="text-abyss-400 text-sm mb-1 flex-shrink-0">过去7天</div>
            <div class="w-full flex-1">
              <v-chart :init-options="{}" :option="trendOption?.active_accounts_trend" :autoresize="true" />
            </div>
          </div>
          <div class="flex flex-col glass metal-border rounded-xl p-5 h-[300px]">
            <div class="flex items-center gap-2 mb-1 flex-shrink-0">
              <div class="text-abyss-800 font-bold">平均会话互动数</div>
              <a-tooltip content="反映每个会话用户的持续沟通次数，如果用户与 AI 进行了 10 轮对话，即为 10，该指标反映了用户粘性。">
                <icon-question-circle-fill class="text-gold-300" />
              </a-tooltip>
            </div>
            <div class="text-abyss-400 text-sm mb-1 flex-shrink-0">过去7天</div>
            <div class="w-full flex-1">
              <v-chart :init-options="{}" :option="trendOption?.avg_of_conversation_messages_trend" :autoresize="true" />
            </div>
          </div>
          <div class="flex flex-col glass metal-border rounded-xl p-5 h-[300px]">
            <div class="flex items-center gap-2 mb-1 flex-shrink-0">
              <div class="text-abyss-800 font-bold">费用消耗</div>
              <a-tooltip content="反映每日该应用请求语言模型的 Tokens 花费，用于成本控制。">
                <icon-question-circle-fill class="text-gold-300" />
              </a-tooltip>
            </div>
            <div class="text-abyss-400 text-sm mb-1 flex-shrink-0">过去7天</div>
            <div class="w-full flex-1">
              <v-chart :init-options="{}" :option="trendOption?.cost_consumption_trend" :autoresize="true" />
            </div>
          </div>
        </div>
      </a-spin>
    </div>
  </div>
</template>

<style scoped></style>
