/*
 * Copyright (c) 2022 Bohdan Marukhnenko
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

package data

import (
	"github.com/patrickmn/go-cache"
	"strconv"
	"time"
)

// UserDataManager makes it easier to work with user data.
type UserDataManager struct {
	UserId   int64
	Database *Database
}

// UserData is a struct that contains all the data about a user.
type UserData struct {
	UserId       int64     `db:"user_id"`
	FirstName    string    `db:"first_name"`
	LastName     string    `db:"last_name"`
	Username     string    `db:"username"`
	LanguageCode string    `db:"lang_code"`
	IsPremium    bool      `db:"is_premium"`
	IsAdmin      bool      `db:"is_admin"`
	Referral     string    `db:"referral"`
	Created      time.Time `db:"created"`
}

// GetUserData returns user data for the user.
func (m *UserDataManager) GetUserData() (*UserData, error) {
	log.Debugf("Getting user data for user %d\n", m.UserId)

	// Get from cache
	cachedData, ok := userCache.Get(strconv.FormatInt(m.UserId, 10))
	if ok {
		return cachedData.(*UserData), nil
	}

	// Get from database
	userData := new(UserData)
	err := m.Database.Db.Get(userData, GetUserQuery, m.UserId)
	if err != nil {
		return nil, err
	}

	// Add to cache
	err = userCache.Add(strconv.FormatInt(m.UserId, 10), userData, cache.DefaultExpiration)
	if err != nil {
		return nil, err
	}

	return userData, nil
}

// UpdateUserData updates user data for the user.
func (m *UserDataManager) UpdateUserData(userData *UserData) error {
	log.Debugf("Updating user data for user %d\n", userData.UserId)

	_, err := m.Database.Db.NamedExec(UpdateUserQuery, userData)
	if err != nil {
		return err
	}

	return nil
}

// CreateUserData creates user data for the user.
func (m *UserDataManager) CreateUserData() (*UserData, error) {
	log.Debugf("Creating user data for user %d\n", m.UserId)

	userData := new(UserData)
	err := m.Database.Db.Get(userData, CreateUserQuery, m.UserId)
	if err != nil {
		return nil, err
	}

	return userData, nil
}

// IsUserExists checks if the user exists in the database.
func (m *UserDataManager) IsUserExists() (bool, error) {
	log.Debugf("Checking if user %d exists\n", m.UserId)

	// Check from cache
	_, ok := userCache.Get(strconv.FormatInt(m.UserId, 10))
	if ok {
		return true, nil
	}

	// Check from database
	var exists bool
	err := m.Database.Db.Get(&exists, IsUserExistsQuery, m.UserId)
	if err != nil {
		return false, err
	}

	return exists, nil
}

// GetOrCreateUserData returns user data for the user or creates it if it doesn't exist.
func (m *UserDataManager) GetOrCreateUserData() (*UserData, error) {
	// Check if user data exists
	exists, err := m.IsUserExists()
	if err != nil {
		return nil, err
	}

	// If user data doesn't exist, create it
	if !exists {
		userData, err := m.CreateUserData()
		if err != nil {
			return nil, err
		}
		return userData, nil
	}

	// Get user data
	userData, err := m.GetUserData()
	if err != nil {
		return nil, err
	}

	return userData, nil
}
