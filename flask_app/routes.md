
<!-- admin page -->

<!-- <form action="/logout" method="POST"> -->
                    <!-- <form action="/submit" method="POST"> -->
<!-- <form action="/createUser" method="POST"> -->
<!-- <form action="/deleteUser" method="POST"> -->
<!-- <form action="/togglePortal"> -->
<!-- <form action="/setGroupSize"> -->
<!-- <form action="/setProjectList"> -->
<!-- <form action="/setAdminPassword"> -->
<form action="/doComputation">
<!-- <form action="/resetPortal"> -->

/ConfirmSubmissionTeacher
/finalSubmitTeacher

<!-- user page -->

<form action="/logout">
<!-- <form action="/ConfirmSubmission"> -->
<!-- <form action="/selectMembers"> -->



## TO DO
<!-- 1. result page for admin -->
<!-- 2. remove set project list option -> remove all users - not required now -->
1. sort the userlist file using CPI
<!-- 3. result page for professor -->
<!-- 4. break admin page into multiple pages -->
5. fix navbar for responsive behaviour
<!-- 6. find pdf api -->
<!-- 7. confirmation modals for teacher pages -->
8. optimise xls (cache files)
9. add check for primary key in userlist file upload
10. why send to all? -> group members should be satisfied with each other, not just with the leader
11. why did you randomly choose extra_student number of first slotters and increased their group size ->wouln't those extra_students want to be open to all group leaders?.....no leader would want to have a larger group.
12. show student list on teacher pages
<!-- 13. show slot number on admin page view users -->
<!-- 8. front end checks, DB checks if user/teacher already exists -->
<!-- 2. add route for teacher finalsubmission -->
<!-- 1. add route for teacher confirmation -->
<!-- 3. store project list in portalConfig -->
<!-- 4. store student list in portalConfig -->
<!-- 5. Add option on admin page to add/delete a professor -->
<!-- 7. result page for student -->
<!-- 10. fix reset project list option -->



## Frontend New TODO

1. sort userlist input file before adding to database
2. change password on every page
3. improve all students page
4. add all students page to admin page
5. Reorganise divs on manage users(rename to manage faculty) page
6. after leader sends request to a tentative group, show that group's information(improve this page)
7. add check on delete/add faculty and current project list reset if a student has made a subject preference submission
8. make the header image less tall


## Advanced feature

1. on compute -> find all those leaders whose groups have not yet been finalised
2. randomly form groups
3. and then compute