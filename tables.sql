CREATE TABLE IF NOT EXISTS Departments(
	dep_id SERIAL PRIMARY KEY,
	dep_name VARCHAR(100) UNIQUE NOT NULL,
	-- total funds
	budget_limit NUMERIC(15,2) NOT NULL,
	current_balance NUMERIC(15,2)
);


CREATE TABLE IF NOT EXISTS Users(
	user_id SERIAL PRIMARY KEY,
	user_name VARCHAR(50) NOT NULL,
	-- login
	user_email VARCHAR(100) UNIQUE NOT NULL,
	-- 'Employee',manager
	user_role VARCHAR(50) NOT NULL CHECK (user_role IN('Employee','Manager','Admin')),
	dept_id INT NOT NULL,
	FOREIGN KEY (dept_id) REFERENCES Departments(dep_id)
);



CREATE TABLE IF NOT EXISTS Expense_Categories(
	cat_id SERIAL PRIMARY KEY,
	-- 'Travel','Equipment'
	cat_name VARCHAR(50) NOT NULL,  
	description TEXT
);

-- interacts with firedatabase
CREATE TABLE IF NOT EXISTS Expense_Claims(
	claim_id SERIAL PRIMARY KEY,
	-- amount requested
	amount NUMERIC(15,2) NOT NULL,
	-- pending,rejected, approved
	status VARCHAR(50) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Rejected', 'Under_Review')),
	-- url for image
	receipt_url TEXT NOT NULL,
	submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	-- who made claim
	user_id INT NOT NULL,
	FOREIGN KEY (user_id) REFERENCES Users(user_id),
	-- category of spending
	cat_id INT NOT NULL,
	FOREIGN KEY (cat_id) REFERENCES Expense_Categories(cat_id),
	dept_id INT NOT NULL,
	FOREIGN KEY (dept_id) REFERENCES Departments(dep_id)
);

CREATE TABLE IF NOT EXISTS Verified_Transaction(
	trx_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	claim_id INT NOT NULL,
	FOREIGN KEY (claim_id) REFERENCES Expense_Claims(claim_id),
	final_amount NUMERIC(15,2) NOT NULL CHECK (final_amount > 0),
	verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	verified_by INT NOT NULL,
	FOREIGN KEY (verified_by) REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS Audit_Trail(
	log_id BIGSERIAL PRIMARY KEY,
	target_table VARCHAR(50) NOT NULL,
	operation VARCHAR(50) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
	old_data JSONB,
	new_data JSONB,
	-- user_id who authorized it
	user_id INT NOT NULL,
	FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
