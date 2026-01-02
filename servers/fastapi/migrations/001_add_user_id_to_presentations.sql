-- Drop column if it exists from previous attempt
ALTER TABLE presentations DROP COLUMN IF EXISTS user_id;

-- Add user_id column to presentations table (UUID to match user.id type)
ALTER TABLE presentations ADD COLUMN user_id UUID;

-- Add foreign key constraint
ALTER TABLE presentations 
ADD CONSTRAINT fk_presentations_user 
FOREIGN KEY (user_id) REFERENCES "user"(id) 
ON DELETE CASCADE;

-- Create index for faster lookups
CREATE INDEX idx_presentations_user_id ON presentations(user_id);
