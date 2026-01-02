class DatabaseError(Exception):
    """Base class for my application's database-related errors."""
    pass


class ActorNotFoundError(DatabaseError):
    def __init__(self, actor_id: int):
        """Exception raised when an actor is not found."""
        self.actor_id = actor_id
        self.message = f"Actor with ID {actor_id} not found"
        super().__init__(self.message)


class MovieNotFoundError(DatabaseError):
    def __init__(self, movie_id: int):
        """Exception raised when a movie is not found."""
        self.movie_id = movie_id
        self.message = f"Movie with ID {movie_id} not found"
        super().__init__(self.message)
