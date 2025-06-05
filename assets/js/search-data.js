// get the ninja-keys element
const ninja = document.querySelector('ninja-keys');

// add the home and posts menu items
ninja.data = [{
    id: "nav-about",
    title: "about",
    section: "Navigation",
    handler: () => {
      window.location.href = "/";
    },
  },{id: "nav-people",
          title: "people",
          description: "our team",
          section: "Navigation",
          handler: () => {
            window.location.href = "/people/";
          },
        },{id: "nav-teaching",
          title: "teaching",
          description: "at the University of Arizona",
          section: "Navigation",
          handler: () => {
            window.location.href = "/teaching/";
          },
        },{id: "news-guangyu-presents-graph-neural-networks-for-polycrystals-at-the-machine-learning-and-simulations-seesion-of-the-mrs-spring-meeting-in-seattle-wa",
          title: 'Guangyu presents graph neural networks for polycrystals at the Machine Learning and Simulations...',
          description: "",
          section: "News",},{id: "news-a-new-preprint-on-modeling-fatigue-indicators-parameters-with-graph-neural-networks-is-live-on-arxiv",
          title: 'A new preprint on modeling fatigue indicators parameters with graph neural networks is...',
          description: "",
          section: "News",},{id: "news-sheila-gives-an-oral-presentation-on-modeling-microstructure-property-relationships-of-materials-with-transformers-at-a-cvpr-workshop-in-seattle-wa",
          title: 'Sheila gives an oral presentation on modeling microstructure–property relationships of materials with transformers...',
          description: "",
          section: "News",},{id: "news-our-paper-on-graph-neural-networks-for-polycrystals-is-published-in-computational-materials-science",
          title: 'Our paper on graph neural networks for polycrystals is published in Computational Materials...',
          description: "",
          section: "News",},{id: "news-marat-joins-los-alamos-national-lab-for-a-summer-month-as-an-isti-distinguished-faculty-scholar",
          title: 'Marat joins Los Alamos National Lab for a summer month as an ISTI...',
          description: "",
          section: "News",},{id: "news-dr-jiayang-wang-from-penn-state-joins-us-as-a-postdoctoral-research-associate-welcome-jiayang",
          title: 'Dr. Jiayang Wang from Penn State joins us as a postdoctoral research associate....',
          description: "",
          section: "News",},{id: "news-thomas-is-selected-for-a-sulzer-mines-scholarship-congratulations",
          title: 'Thomas is selected for a Sulzer Mines Scholarship. Congratulations!',
          description: "",
          section: "News",},{id: "news-new-students-eric-hao-saege-i-tzu-and-aditya-join-the-group-welcome",
          title: 'New students: Eric, Hao, Saege, I-Tzu, and Aditya join the group. Welcome!',
          description: "",
          section: "News",},{id: "news-a-new-preprint-on-spatially-resolved-chord-length-distribtuions-is-live-on-arxiv",
          title: 'A new preprint on spatially resolved chord length distribtuions is live on arXiv!...',
          description: "",
          section: "News",},{id: "news-we-now-accept-applications-from-mse-undergrads-for-2025-materialz-winter-school",
          title: 'We now accept applications from MSE undergrads for 2025 MateriAlZ Winter School!',
          description: "",
          section: "News",},{id: "news-our-work-on-gnns-predicting-fips-in-large-polycrystals-is-now-published-in-scripta-materialia",
          title: 'Our work on GNNs predicting FIPs in large polycrystals is now published in...',
          description: "",
          section: "News",},{id: "news-thomas-presents-his-research-on-accelerated-design-of-sustainable-concrete-at-aci-concrete-convention-in-philadelphia-pa",
          title: 'Thomas presents his research on accelerated design of sustainable concrete at ACI Concrete...',
          description: "",
          section: "News",},{id: "news-sheila-passes-comprehensive-exam-in-applied-math-gidp-congratulations",
          title: 'Sheila passes comprehensive exam in Applied Math GIDP. Congratulations!',
          description: "",
          section: "News",},{id: "news-marat-receives-the-nsf-career-award-that-will-support-fundamental-research-of-damage-in-sustainable-aluminum-alloys-and-mgi-workforce-development",
          title: 'Marat receives the NSF CAREER award that will support fundamental research of damage...',
          description: "",
          section: "News",},{id: "news-a-new-preprint-on-machine-learning-of-properties-with-microstructure-description-using-vision-transformers-is-live-on-arxiv",
          title: 'A new preprint on machine learning of properties with microstructure description using vision...',
          description: "",
          section: "News",},{id: "news-guangyu-submits-a-solution-to-an-industry-problem-as-part-of-applied-math-hackathon",
          title: 'Guangyu submits a solution to an industry problem as part of applied math...',
          description: "",
          section: "News",handler: () => {
              window.location.href = "/news/250318_guangyu-solution/";
            },},{id: "news-sheila-gives-an-invited-seminar-at-the-materials-informatics-webinar-organized-by-nasa-glenn-research-center",
          title: 'Sheila gives an invited seminar at the Materials Informatics Webinar organized by NASA...',
          description: "",
          section: "News",},{id: "news-guangyu-presents-his-research-on-graph-neural-networks-at-the-mse-graduate-seminar",
          title: 'Guangyu presents his research on graph neural networks at the MSE Graduate Seminar....',
          description: "",
          section: "News",},{id: "news-thomas-defends-his-master-s-thesis-on-accelerated-design-of-sustainable-concrete",
          title: 'Thomas defends his Master’s thesis on accelerated design of sustainable concrete.',
          description: "",
          section: "News",},{id: "news-samiah-defends-her-master-s-thesis-on-eutectic-and-peritectic-equilibria-in-coherent-binary-alloys",
          title: 'Samiah defends her Master’s thesis on eutectic and peritectic equilibria in coherent binary...',
          description: "",
          section: "News",},{id: "news-marat-gives-a-seminar-at-the-applied-math-program-on-selected-problems-in-materials-informatics",
          title: 'Marat gives a seminar at the Applied Math program on selected problems in...',
          description: "",
          section: "News",},{id: "news-thomas-team-wins-the-second-prize-at-the-mit-water-food-amp-amp-agricalture-innovation-competition",
          title: 'Thomas’ team wins the second prize at the MIT Water, Food, &amp;amp;amp; Agricalture...',
          description: "",
          section: "News",},{id: "news-sheila-receives-the-herbert-e-carter-travel-award-to-present-at-the-tms-specialty-congress",
          title: 'Sheila receives the Herbert E. Carter Travel Award to present at the TMS...',
          description: "",
          section: "News",},{id: "projects-guangyu-hu",
          title: 'Guangyu Hu',
          description: "Materials Science and Engineering",
          section: "Projects",handler: () => {
              window.location.href = "/projects/Guangyu/";
            },},{id: "projects-i-tzu-huang",
          title: 'I-Tzu Huang',
          description: "Physics",
          section: "Projects",handler: () => {
              window.location.href = "/projects/I-Tzu/";
            },},{id: "projects-jiayang-wang",
          title: 'Jiayang Wang',
          description: "Materials Science and Engineering",
          section: "Projects",handler: () => {
              window.location.href = "/projects/Jiayang/";
            },},{id: "projects-jordan-casto",
          title: 'Jordan Casto',
          description: "Mechanical Engineering",
          section: "Projects",handler: () => {
              window.location.href = "/projects/Jordan/";
            },},{id: "projects-marat-latypov",
          title: 'Marat Latypov',
          description: "MSE and Applied Mathematics",
          section: "Projects",handler: () => {
              window.location.href = "/projects/Marat/";
            },},{id: "projects-sheila-whitman",
          title: 'Sheila Whitman',
          description: "Applied Mathematics",
          section: "Projects",handler: () => {
              window.location.href = "/projects/Sheila/";
            },},{id: "projects-thomas-tawiah-baah",
          title: 'Thomas Tawiah Baah',
          description: "Materials Science and Engineering",
          section: "Projects",handler: () => {
              window.location.href = "/projects/Thomas/";
            },},{id: "projects-tommy-dracopoulos",
          title: 'Tommy Dracopoulos',
          description: "Mechanical Engineering",
          section: "Projects",handler: () => {
              window.location.href = "/projects/Tommy/";
            },},{id: "projects-samiah-hassan",
          title: 'Samiah Hassan',
          description: "M.S. thesis research",
          section: "Projects",handler: () => {
              window.location.href = "/projects/xSamiah/";
            },},{
        id: 'social-email',
        title: 'email',
        section: 'Socials',
        handler: () => {
          window.open("mailto:%6C%61%74%6D%61%72%61%74@%61%72%69%7A%6F%6E%61.%65%64%75", "_blank");
        },
      },{
        id: 'social-scholar',
        title: 'Google Scholar',
        section: 'Socials',
        handler: () => {
          window.open("https://scholar.google.com/citations?user=We5aJywAAAAJ", "_blank");
        },
      },{
      id: 'light-theme',
      title: 'Change theme to light',
      description: 'Change the theme of the site to Light',
      section: 'Theme',
      handler: () => {
        setThemeSetting("light");
      },
    },
    {
      id: 'dark-theme',
      title: 'Change theme to dark',
      description: 'Change the theme of the site to Dark',
      section: 'Theme',
      handler: () => {
        setThemeSetting("dark");
      },
    },
    {
      id: 'system-theme',
      title: 'Use system default theme',
      description: 'Change the theme of the site to System Default',
      section: 'Theme',
      handler: () => {
        setThemeSetting("system");
      },
    },];
