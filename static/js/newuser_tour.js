// Instance the tour
var tour = new Tour({
    steps: [
    {
      element: "#recently-uploaded-text",
      title: "Title of my step",
      content: "Content of my step"
    },
    {
      element: "#new-user-box",
      title: "Title of my next step",
      content: "Content of my next step"
    },
    {
      path: "/problems",
      element: "#myTable",
      title: "testing the different page tour",
      content: "Content of my next step"
    }
  ]});
  
  // Initialize the tour
  tour.init();
  
  // Start the tour
  tour.start();