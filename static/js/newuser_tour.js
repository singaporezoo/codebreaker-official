var tour = new Tour({
  steps: [
  {
    path: "/?tour=true",
    element: "#problems-card",
    title: "Practice Makes Perfect",
    content: "Let's start by viewing the list of problems on Codebreaker! If you wish, you can sort by newest or unsolved, or even try out our problem recommendation algorithm.",
    placement: "auto"
  },
  {
    path: "/problems",
    element: "#filter-problems-card",
    title: "Filter by Tags",
    content: "Here, you can filter the list of problems by tags/topics...",
    placement: "auto"
  },
  {
    path: "/problems",
    element: "#myInput",
    title: "Search Problems",
    content: "...or search for a problem name/author/source directly!",
    placement: "auto"
  },
  {
    path: "/problem/helloworld",
    element: "#problem-tab-content",
    title: "Example Problem",
    content: "On this page, you can view the problem statement on the left...",
    placement: "auto"
  },
  {
    path: "/problem/helloworld",
    element: "#problem-right-column",
    title: "Example Problem",
    content: "...along with other problem details in the column on the right.",
    placement: "auto"
  },
  {
    path: "/problem/helloworld",
    element: "#problem-all-tabs",
    title: "Problem Tabs",
    content: "To submit your code, just click the 'Submit Code' tab and use our code editor. You can also view submissions to this problem using the other tabs.",
    placement: "auto"
  },
  {
    path: "/problem/helloworld",
    orphan: true,
    title: "Next Up: Contests",
    content: "Let's take a look at our next feature - contests.",
    placement: "auto"
  },
  {
    path: "/contests",
    element: "#contest-all-tabs",
    title: "Training Ground",
    content: "Here, you can view past, present or future Codebreaker contests, along with other contests that have been archived, such as past IOI and APIO problems. Public contests or contests you have been added to can also be viewed on the calendar on your homepage.",
    placement: "auto"
  },
  {
    path: "/contests",
    element: "#contest-groups-tab",
    title: "Contest Groups",
    content: "Our contests have been sorted into categories under the Contest Groups tab for your convenience.",
    placement: "auto"
  },
  {
    path: "/contest/dec2020c1",
    orphan: true,
    title: "Example Contest",
    content: "From the main page of a contest, you will be able to see the list of problems and your scores. For ongoing contests, there will also be a countdown timer shown.<br>Speaking of scores, let's see what Codebreaker's submissions look like.",
    placement: "auto"
  },
  {
    path: "/submissions",
    orphan: true,
    title: "Submissions",
    content: "On this page, you can search for submissions by username or problem name, and view the list of submissions with scores and other details.",
    placement: "auto"
  },
  {
    path: "/submission/150361",
    element: "#submission-subtasks-container",
    title: "Submission Feedback",
    content: "Your scores for each subtask will be shown here. Full feedback is available in analysis mode and for certain contests.",
    placement: "auto"
  },
  {
    path: "/?tour=true",
    orphan: true,
    title: "Last Words",
    content: "That's all for our main features for now. Do contact the Codebreaker admins for any further queries.",
    placement: "auto"
  },
  {
    path: "/?tour=true",
    orphan: true,
    title: "End of Tour",
    content: "We hope you have enjoyed this tour and will enjoy the rest of your Codebreaker experience. Thanks, and goodbye!",
    placement: "auto"
  }],
  backdrop: true,
  storage: window.localStorage,
  debug: true,
  framework: "bootstrap4",
  onEnd: function(tour){
    document.location.href="/";
  }
});

