# APSIT Community Backend

Welcome to the APSIT Community Backend repository! This backend server is designed to support the APSIT Community web application, facilitating user authentication, data management, and API endpoints for seamless communication with the frontend.

## Overview

The APSIT Community Backend is a Python-based server application developed to empower the [APSIT Community](https://github.com/VaidikV/APSIT_Community) web platform. It ensures secure user authentication, manages posts and comments, and enables real-time messaging.

## Features

The APSIT Community Backend provides a comprehensive set of features to support the APSIT Community web application:

### User Authentication and Management

1. **Create Account (`/add-user`):**
   - Allows users to create an account with APSIT Community.
   - Utilizes secure password hashing using Flask-Bcrypt.
   - Generates a JWT token for authentication.

2. **Log In (`/find-user`):**
   - Enables users to log in securely.
   - Validates credentials against stored hashed passwords.
   - Issues a JWT token upon successful login.

3. **Update User Information (`/update-user`):**
   - Permits users to update their account details.
   - Requires authentication through a valid JWT token.

4. **Delete User Account (`/delete-user`):**
   - Allows users to delete their APSIT Community account.
   - Requires authentication through a valid JWT token.

### Calendar and Events

5. **Add Event (`/add-event`):**
   - Enables users to add events to their calendar.
   - Filters profane content from event details.

6. **Delete Event (`/delete-event`):**
   - Allows users to remove events from their calendar.

7. **Fetch User Events (`/events`):**
   - Retrieves events associated with the authenticated user.

### Post Management

8. **Create Post (`/create-post`):**
   - Allows users to create new posts.
   - Filters profane content from post details.

9. **Read Posts (`/posts`):**
   - Retrieves a list of posts, excluding sensitive information.
   - Sorted in descending order based on creation time.

10. **Read Specific Post (`/post`):**
    - Fetches details of a specific post based on the post ID.

11. **Edit Post (`/edit-post`):**
    - Allows users to edit their existing posts.
    - Filters profane content from updated post details.

12. **Delete Post (`/delete-post`):**
    - Enables users to delete their posts.

13. **User's Posts (`/user-post`):**
    - Retrieves all posts created by a specific user.

14. **Add Comment (`/post/comments`):**
    - Allows users to add comments to posts.
    - Filters profane content from comments.

15. **Reply to Comment (`/post/replycomment`):**
    - Permits users to reply to existing comments.
    - Filters profane content from replies.

16. **Like/Unlike Post (`/post/like`):**
    - Allows users to like or unlike a post.

17. **Bookmark Post (`/post/bookmark`):**
    - Enables users to bookmark or unbookmark a post.

18. **Report Post (`/post/report`):**
    - Allows users to report inappropriate posts.

### Internship and News API

19. **Fetch Internships (`/internships`):**
    - Retrieves internships based on the specified domain.

20. **Fetch News (`/news/all`):**
    - Retrieves the latest news articles.

### General Tools

21. **Token Validation (`/get-user`):**
    - Verifies JWT tokens for authentication.
    - Fetches user information based on the provided token.

22. **JSON Conversion (`jsoner`):**
    - Converts BSON data to JSON format.

23. **Profanity Filtering:**
    - Filters out profane content from various inputs.

24. **Error Handling:**
    - Provides meaningful error messages for different scenarios.

The backend is built using Flask and MongoDB, integrating security measures and ensuring the robust functioning of the APSIT Community web application.

