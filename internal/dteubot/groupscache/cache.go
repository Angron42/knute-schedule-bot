// What it does?
//   Provides cache for groups to get group name by id
// Why it's needed?
//   Because API doesn't provide any way to get group name by id, but
//   we need to show it for example in settings menu

package groupscache

import (
	"encoding/csv"
	"github.com/cubicbyte/dteubot/pkg/api/cachedapi"
	"github.com/op/go-logging"
	"io"
	"os"
	"strconv"
	"time"
)

var log = logging.MustGetLogger("GroupsCache")

const TTL = 60 * 60 * 24 // 1 day

type Group struct {
	Id        int
	Name      string
	Course    int
	FacultyId int
	Updated   int64
}

type Cache struct {
	File   string
	groups map[int]Group
	api    *cachedapi.CachedApi
}

// New creates new cache instance
func New(file string, apiInstance *cachedapi.CachedApi) *Cache {
	return &Cache{
		File:   file,
		groups: make(map[int]Group),
		api:    apiInstance,
	}
}

func (c *Cache) AddGroups(groups []Group) error {
	for _, group := range groups {
		c.groups[group.Id] = group
	}

	return c.Save()
}

func (c *Cache) AddGroup(group Group) error {
	c.groups[group.Id] = group

	return c.Save()
}

func (c *Cache) GetGroup(id int) (*Group, error) {
	log.Debugf("Getting group %d\n", id)

	group, ok := c.groups[id]
	if !ok {
		return nil, nil
	}

	// Check if group is outdated
	timestamp := time.Now().Unix()
	if timestamp-group.Updated > TTL {
		// Update group
		newGroup, err := c.updateGroup(group)
		if err != nil {
			if ok {
				// Return old group if update failed
				return &group, err
			}
			return nil, err
		}

		return newGroup, nil
	}

	return &group, nil
}

func (c *Cache) updateGroup(group Group) (*Group, error) {
	log.Debugf("Updating group %d\n", group.Id)

	// Get group from api at current course
	groups, err := c.api.GetGroups(group.FacultyId, group.Course)
	if err != nil {
		return nil, err
	}

	for _, g := range groups {
		if g.Id == group.Id {
			// Update group
			group.Name = g.Name
			group.Updated = time.Now().Unix()

			// Save cache
			err := c.Save()
			if err != nil {
				return nil, err
			}

			return &group, nil
		}
	}

	// Group not found. Try to find group at next courses
	courses, err := c.api.GetCourses(group.FacultyId)
	if err != nil {
		return nil, err
	}

	for _, course := range courses {
		if course.Course <= group.Course {
			continue
		}

		groups, err := c.api.GetGroups(group.FacultyId, course.Course)
		if err != nil {
			return nil, err
		}

		for _, g := range groups {
			if g.Id == group.Id {
				// Update group
				group.Name = g.Name
				group.Course = course.Course
				group.Updated = time.Now().Unix()

				// Save cache
				err := c.Save()
				if err != nil {
					return nil, err
				}

				return &group, nil
			}
		}
	}

	// Group not found at all courses
	return nil, nil
}

// Load cache from csv file
//
// File format:
//
//	id;name;course;faculty_id;updated
func (c *Cache) Load() error {
	log.Infof("Loading groups cache from %s\n", c.File)

	// Open csv file
	f, err := os.OpenFile(c.File, os.O_RDWR|os.O_CREATE, 0666)
	if err != nil {
		return err
	}

	// Read file
	reader := csv.NewReader(f)
	reader.Comma = ';'

	// Read all records
	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			if err := f.Close(); err != nil {
				return err
			}
			return err
		}

		// Parse group
		id, err := strconv.Atoi(record[0])
		if err != nil {
			return err
		}
		course, err := strconv.Atoi(record[2])
		if err != nil {
			return err
		}
		facultyId, err := strconv.Atoi(record[3])
		if err != nil {
			return err
		}
		updated, err := strconv.ParseInt(record[4], 10, 64)
		if err != nil {
			return err
		}

		group := Group{
			Id:        id,
			Name:      record[1],
			Course:    course,
			FacultyId: facultyId,
			Updated:   updated,
		}

		c.groups[id] = group
	}

	return f.Close()
}

// Save cache to csv file
func (c *Cache) Save() error {
	log.Debugf("Saving groups cache to %s\n", c.File)

	// Open csv file
	f, err := os.OpenFile(c.File, os.O_RDWR|os.O_CREATE, 0666)
	if err != nil {
		return err
	}

	// Create csv writer
	writer := csv.NewWriter(f)
	writer.Comma = ';'

	// Write all groups
	for _, group := range c.groups {
		err := writer.Write([]string{
			strconv.Itoa(group.Id),
			group.Name,
			strconv.Itoa(group.Course),
			strconv.Itoa(group.FacultyId),
			strconv.FormatInt(group.Updated, 10),
		})
		if err != nil {
			return err
		}
	}

	// Flush csv writer
	writer.Flush()

	return f.Close()
}