import type gsap from 'gsap'
import type ScrollTrigger from 'gsap/ScrollTrigger'

declare module '#app' {
  interface NuxtApp {
    $gsap: typeof gsap
    $ScrollTrigger: typeof ScrollTrigger
  }
}

export {}
