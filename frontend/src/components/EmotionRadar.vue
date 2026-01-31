<template>
  <div ref="chartRef" class="w-full h-full"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import * as echarts from 'echarts';

// 接收父组件传过来的情感向量
const props = defineProps({
  vector: {
    type: Object,
    default: () => ({ "喜悦": 0, "信任": 0, "恐惧": 0, "惊讶": 0, "悲伤": 0, "厌恶": 0, "愤怒": 0, "期待": 0 })
  }
});

const chartRef = ref(null);
let myChart = null;

onMounted(() => {
  myChart = echarts.init(chartRef.value);
  updateChart();
});

// 监听数据变化，实时更新图表（实现“跳动感”）
watch(() => props.vector, () => {
  updateChart();
}, { deep: true });

const updateChart = () => {
  if (!myChart) return;
  
  const option = {
    backgroundColor: 'transparent',
    radar: {
      indicator: [
        { name: '喜悦', max: 10 }, { name: '信任', max: 10 },
        { name: '恐惧', max: 10 }, { name: '惊讶', max: 10 },
        { name: '悲伤', max: 10 }, { name: '厌恶', max: 10 },
        { name: '愤怒', max: 10 }, { name: '期待', max: 10 }
      ],
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#666', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: [
          props.vector['喜悦'], props.vector['信任'], props.vector['恐惧'], props.vector['惊讶'],
          props.vector['悲伤'], props.vector['厌恶'], props.vector['愤怒'], props.vector['期待']
        ],
        name: '实时情感',
        symbol: 'none',
        itemStyle: { color: '#22d3ee' }, // 这里的颜色以后可以动态根据情绪变色
        areaStyle: {
          color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
            { color: 'rgba(34, 211, 238, 0.6)', offset: 0 },
            { color: 'rgba(34, 211, 238, 0)', offset: 1 }
          ])
        },
        lineStyle: { width: 2, opacity: 0.8 }
      }]
    }]
  };
  myChart.setOption(option);
};
</script>