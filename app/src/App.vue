<template>
  <div id="app">
    <div v-if="isLoading">Loading...</div>
    <div>
      <label for="file">Upload your custom CSV..</label>
      <input id="file" type="file" @change="uploadFile" />
    </div>
    <div>
      <label>Filter flipper length (min):</label>
      <input type="range" v-model="flipperLengthMin" min="0" max="250" />
      <span>{{ flipperLengthMin }}</span>
    </div>
    <div>
      <label>Choose Plot Type:</label>
      <select v-model="selectedPlot">
        <option value="scatter">Scatter Plot</option>
        <option value="histogram">Histogram</option>
      </select>
    </div>
    <div id="plotly-container">
      <plotly :data="plotData" :layout="layout"></plotly>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from "vue";
import axios from "axios";
import { VuePlotly as Plotly } from "@clalarco/vue3-plotly";

function debounce(fn, delay) {
  let timeoutID;
  return function (...args) {
    clearTimeout(timeoutID);
    timeoutID = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
}

export default {
  name: "App",
  components: {
    Plotly,
  },
  setup() {
    const flipperLengthMin = ref(100);
    const selectedPlot = ref("scatter");
    const plotData = ref([]);
    const layout = ref({});
    const isLoading = ref(false);

    const uploadFile = (event) => {
      const file = event.target.files[0];
      const formData = new FormData();
      formData.append("file", file);
      axios
        .post("http://localhost:8000/upload/", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        })
        .then(() => {
          fetchPlot();
        });
    };

    const fetchPlot = async () => {
      const url =
        selectedPlot.value === "scatter"
          ? `http://localhost:8000/scatter-plot?x=bill_length_mm&y=bill_depth_mm&color=species&flipper_length_min=${flipperLengthMin.value}`
          : `http://localhost:8000/histogram?column=bill_length_mm&color=species&flipper_length_min=${flipperLengthMin.value}`;

      try {
        isLoading.value = true;
        const json = await axios.get(url);
        const { data, layout } = JSON.parse(json.data) ?? {};
        isLoading.value = false;
        plotData.value = data;
        layout.value = layout;
      } catch (err) {
        isLoading.value = false;
        console.error(err, "error");
      }
    };

    const debouncedFetchPlot = debounce(fetchPlot, 300);

    watch([flipperLengthMin, selectedPlot], debouncedFetchPlot);

    onMounted(fetchPlot);

    return {
      flipperLengthMin,
      selectedPlot,
      plotData,
      layout,
      uploadFile,
      isLoading,
    };
  },
};
</script>

<style>
#app {
  text-align: center;
  margin-top: 50px;
}
#plotly-container {
  width: calc(80vw);
  height: 500px;
}
</style>
