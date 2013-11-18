
class CommitHolder():

    def __init__(self, pygit_commit):
        self.author = pygit_commit.author.name
        self.hex = pygit_commit.hex
        self.message = pygit_commit.message
        from datetime import datetime
        # TODO take into account commit_time_offset
        self.time_committed = datetime.fromtimestamp(pygit_commit.commit_time)


class DiffHolder():

    def __init__(self, pygit_diff):
        self.patches = [PatchHolder(p) for p in pygit_diff]

    def __iter__(self):
        return iter(self.patches)


class PatchHolder():

    def __init__(self, pygit_patch):
        self.old_file_path = pygit_patch.old_file_path
        self.new_file_path = pygit_patch.new_file_path
        self.hunks = [HunkHolder(h) for h in pygit_patch.hunks]

    def __iter__(self):
        return iter(self.hunks)


class HunkHolder():

    def __init__(self, pygit_hunk):
        self.old_start = pygit_hunk.old_start
        self.old_line_count = pygit_hunk.old_lines
        self.new_start = pygit_hunk.new_start
        self.new_line_count = pygit_hunk.new_lines
        self.lines = []
        old, new = self.old_start, self.new_start
        for act, line in pygit_hunk.lines:
            line_holder = LineHolder(line, act)
            if line_holder.is_addition:
                line_holder.old_line_number = None
                line_holder.new_line_number = new
                new += 1
            elif line_holder.is_deletion:
                line_holder.old_line_number = old
                line_holder.new_line_number = None
                old += 1
            else:
                line_holder.old_line_number = old
                line_holder.new_line_number = new
                old += 1
                new += 1
            self.lines.append(line_holder)

    def __iter__(self):
        return iter(self.lines)


class LineHolder():

    def __init__(self, line, act):
        self.line = line
        self.act = act
        self.old_line_number = 0
        self.new_line_number = 0

    @property
    def is_addition(self):
        """
        Checks if act string, is "+" representing an addition in pygit line
        """
        return self.act == "+"

    @property
    def is_deletion(self):
        """
        Checks if act string, is "-" representing a deletion in pygit line
        """
        return self.act == "-"
