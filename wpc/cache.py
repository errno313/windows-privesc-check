from wpc.sd import sd
#from wpc.file import file as wpcfile
import wpc.file
import win32net
import win32netcon
import win32security
# Basically a huge hash of all lookups
#
# There should be only one instance of the cache which is started when the script is initialised
# All classes are hard-coded to use this instance of "cache"
#
# wpc.cache # single global instance of this class
#
# Some attributes of "cache" determine how it behaves
# wpc.conf.cache...
class cache:
	def __init__(self):
		self.namefromsid = {}
		self.sidfromname = {}
		self.stringfromsid = {}
		self.sidingroup = {}
		self.files = {}
		self.regkeys = {}
		self.misses = {}
		self.hits = {}
		self.hits['files'] = 0
		self.misses['files'] = 0
		self.hits['regkeys'] = 0
		self.misses['regkeys'] = 0
		self.hits['sd'] = 0
		self.misses['sd'] = 0
		self.hits['LookupAccountSid'] = 0
		self.misses['LookupAccountSid'] = 0
		self.hits['LookupAccountName'] = 0
		self.misses['LookupAccountName'] = 0
		self.hits['is_in_group'] = 0
		self.misses['is_in_group'] = 0
	
	def print_stats(self):
		for k in self.hits.keys():
			print "Hits for %s: %s" % (k, self.get_hits(k))
			print "Misses for %s: %s" % (k, self.get_misses(k))
	
	def sd(self, type, name):
		# TODO caching code here
		return sd(type, name)

	def File(self, name):
		f = None # might save 1 x dict lookup
		if name in self.files.keys():
			#print "[D] Cache hitx for: " + self.files[name].get_name()
			self.hit('files')
			return self.files[name]
		else:
			self.miss('files')
			f = wpc.file.file(name)
			self.files[name] = f
		return f
	
	def regkey(self, name):
		f = None # might save 1 x dict lookup
		if name in self.regkeys.keys():
			#print "[D] Cache hitx for: " + self.files[name].get_name()
			self.hit('regkeys')
			return self.regkeys[name]
		else:
			self.miss('regkeys')
			f = wpc.regkey.regkey(name)
			self.regkeys[name] = f
		return f
	
	def LookupAccountSid(self, server, s):
		sid = win32security.ConvertSidToStringSid(s)
		#print "zzzz"
		if not server in self.namefromsid.keys():
			#print "yyyy"
			self.namefromsid[server] = {}
		if not sid in self.namefromsid[server].keys():
			#print "xxxx %s %s" % (server, sid)
			try:
				self.namefromsid[server][sid] = win32security.LookupAccountSid(server, s)		
			except:
				self.namefromsid[server][sid] = (win32security.ConvertSidToStringSid(s), "[unknown]", 8)
			self.miss('LookupAccountSid')
		else:
			self.hit('LookupAccountSid')
			#print self.namefromsid[server][sid]
		# owner_name, owner_domain, type = 
		
		return self.namefromsid[server][sid]

	def LookupAccountName(self, server, name):
		if not server in self.sidfromname.keys():
			self.sidfromname[server] = {}
		if not name in self.sidfromname[server].keys():
			#print "xxxx %s %s" % (server, name)
			try:
				self.sidfromname[server][name] = win32security.LookupAccountName(server, name)		
			except:
				self.sidfromname[server][name] = None
			self.miss('LookupAccountName')
		else:
			self.hit('LookupAccountName')
			#print self.sidfromname[server][name]
		# owner_name, owner_domain, type = 
		
		return self.sidfromname[server][name]

	def hit(self, name):
		#print "Hit"
		self.hits[name] = self.hits[name] + 1
		
	def miss(self, name):
		#print "Miss"
		self.misses[name] = self.misses[name] + 1
	
	def get_hits(self, name):
		return self.hits[name]
	
	def get_misses(self, name):
		return self.misses[name]
	
	def is_in_group(self, p, group):
		#sid = win32security.ConvertSidToStringSid(s)
		#print "cache.is_in_group called"
		sid = p.get_sid_string()
		if not sid in self.sidingroup.keys():
			self.sidingroup[sid] = {}
		if not group.get_sid_string() in self.sidingroup[sid].keys():
			self.sidingroup[sid][group.get_sid_string()] = 0
			self.miss('is_in_group')
			#print "Miss for is_in_group"
			if p.get_sid_string() in map(lambda x: x.get_sid_string(), group.get_members()):
				self.sidingroup[sid][group.get_sid_string()] = 1
		else:
			#print "Hit for is_in_group"
			self.hit('is_in_group')
		#print "Returning: %s" % self.sidingroup[sid][group.get_sid_string()]
		return self.sidingroup[sid][group.get_sid_string()]

	def NetLocalGroupGetMembers(self, server, name, level):
		keepgoing = 1
		resume = 0
		members = []
		#print "Finding members of %s" % name
		while keepgoing:
			try:
				m, total, resume = win32net.NetLocalGroupGetMembers(server, name, level, resume, win32netcon.MAX_PREFERRED_LENGTH)
			except:
				return []
				
			for member in m:
				members.append(member)
				
			if not resume:
				keepgoing = 0
		#print members
		return members