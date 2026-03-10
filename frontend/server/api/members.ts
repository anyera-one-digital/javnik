const members = [{
  id: 1,
  name: 'Anthony Fu',
  username: 'antfu',
  role: 'member',
  avatar: { src: 'https://ipx.nuxt.com/f_auto,s_192x192/gh_avatar/antfu' },
  specialty: 'Парикмахер',
  servicesCount: 5
}, {
  id: 2,
  name: 'Baptiste Leproux',
  username: 'larbish',
  role: 'member',
  avatar: { src: 'https://ipx.nuxt.com/f_auto,s_192x192/gh_avatar/larbish' },
  specialty: 'Стилист',
  servicesCount: 3
}, {
  id: 3,
  name: 'Benjamin Canac',
  username: 'benjamincanac',
  role: 'owner',
  avatar: { src: 'https://ipx.nuxt.com/f_auto,s_192x192/gh_avatar/benjamincanac' },
  specialty: 'Мастер-колорист',
  servicesCount: 7
}, {
  id: 4,
  name: 'Céline Dumerc',
  username: 'celinedumerc',
  role: 'member',
  avatar: { src: 'https://ipx.nuxt.com/f_auto,s_192x192/gh_avatar/celinedumerc' },
  specialty: 'Парикмахер',
  servicesCount: 4
}, {
  id: 5,
  name: 'Daniel Roe',
  username: 'danielroe',
  role: 'member',
  avatar: { src: 'https://ipx.nuxt.com/f_auto,s_192x192/gh_avatar/danielroe' },
  specialty: 'Барбер',
  servicesCount: 6
}, {
  id: 6,
  name: 'Farnabaz',
  username: 'farnabaz',
  role: 'member',
  avatar: { src: 'https://ipx.nuxt.com/f_auto,s_192x192/gh_avatar/farnabaz' },
  specialty: 'Стилист',
  servicesCount: 3
}, {
  id: 7,
  name: 'Ferdinand Coumau',
  username: 'FerdinandCoumau',
  role: 'member',
  avatar: { src: 'https://ipx.nuxt.com/f_auto,s_192x192/gh_avatar/FerdinandCoumau' },
  specialty: 'Парикмахер',
  servicesCount: 5
}, {
  id: 8,
  name: 'Hugo Richard',
  username: 'hugorcd',
  role: 'owner',
  avatar: { src: 'https://ipx.nuxt.com/f_auto,s_192x192/gh_avatar/hugorcd' },
  specialty: 'Мастер-колорист',
  servicesCount: 8
}, {
  id: 9,
  name: 'Pooya Parsa',
  username: 'pi0',
  role: 'member',
  avatar: { src: 'https://ipx.nuxt.com/f_auto,s_192x192/gh_avatar/pi0' },
  specialty: 'Барбер',
  servicesCount: 4
}, {
  id: 10,
  name: 'Sarah Moriceau',
  username: 'SarahM19',
  role: 'member',
  avatar: { src: 'https://ipx.nuxt.com/f_auto,s_192x192/gh_avatar/SarahM19' },
  specialty: 'Стилист',
  servicesCount: 6
}, {
  id: 11,
  name: 'Sébastien Chopin',
  username: 'Atinux',
  role: 'owner',
  avatar: { src: 'https://ipx.nuxt.com/f_auto,s_192x192/gh_avatar/atinux' },
  specialty: 'Мастер-колорист',
  servicesCount: 9
}]

export default eventHandler(async () => {
  return members
})
