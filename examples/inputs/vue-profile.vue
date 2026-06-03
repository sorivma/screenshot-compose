<script setup lang="ts">
import { computed, ref } from "vue";

const firstName = ref("Ada");
const lastName = ref("Lovelace");
const initials = computed(() => `${firstName.value[0]}${lastName.value[0]}`);
</script>

<template>
  <main class="profile">
    <div class="avatar">{{ initials }}</div>
    <h1>{{ firstName }} {{ lastName }}</h1>
    <button @click="firstName = 'Grace'">Switch user</button>
  </main>
</template>
