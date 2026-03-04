export default defineAppConfig({
  ui: {
    colors: {
      primary: 'lime',
      neutral: 'zinc'
    },
    pageHero: {
      slots: {
        container: 'flex flex-col lg:grid py-8 sm:py-12 lg:py-16 gap-16 sm:gap-y-24'
      }
    },
    button: {
      rounded: 'rounded-[30px]',
      default: {
        rounded: 'rounded-[30px]'
      },
      slots: {
        base: 'rounded-[30px] font-medium inline-flex items-center justify-center disabled:cursor-not-allowed aria-disabled:cursor-not-allowed disabled:opacity-75 aria-disabled:opacity-75 transition-colors'
      }
    }
  }
})
