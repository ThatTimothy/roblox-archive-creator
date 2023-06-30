local process = require("@lune/process")
local fs = require("@lune/fs")
local roblox = require("@lune/roblox")

local HELP = [[Proper usage: lune expand [input] [mode]

input: the file to expand, like place.rbxl
mode: the running mode
    rbxlx: only converts rbxl to rbxlx
    fs_expand: expand scripts in file to the filesystem
    all: enables all of the above
]]

print(process.os)

local function beginsWith(input, ending)
    if #input < #ending then
        return false
    end

    return string.sub(input, 1, #ending) == ending
end

local function endsWith(input, ending)
    if #input < #ending then
        return false
    end

    return string.sub(input, #input - #ending + 1, #input) == ending
end

local function getDir(path: string): string
    path = string.gsub(path, "\\", "/")
    if not beginsWith(path, "./") then
        path = "./" .. path
    end

    local parts = string.split(path, "/")
    table.remove(parts, #parts)

    return table.concat(parts, "/") .. "/"
end

-- Validate arg count
if #process.args ~= 2 then
    error(HELP)
end

local input = process.args[1]
local mode = process.args[2]

-- Validate input
local success, result = pcall(fs.isFile, input)

if not success or not result then
    error(`Could not read file at "{input}"!`)
end

if not endsWith(input, ".rbxl") and not endsWith(input, ".rbxlx") then
    error("Input file provided must be a .rbxl or .rbxlx!")
end

-- Validate mode
local rbxlx = false
local fs_expand = false

if mode == "all" then
    rbxlx = true
    fs_expand = true
elseif mode == "rbxlx" then
    rbxlx = true
elseif mode == "fs_expand" then
    fs_expand = true
else
    error(`Mode "{mode}" is not a valid mode!\n\n`..HELP)
end

print(`Reading "{input}"...`)
local inputFile = fs.readFile(input)
print("Deserializing...")
local game = roblox.deserializePlace(inputFile)

if rbxlx and endsWith(input, ".rbxl") then
    local output = input .. "x"
    print(`rbxlx mode enabled, writing to "{output}"...`)
    local serialized = roblox.serializePlace(game, true)
    fs.writeFile(output, serialized)
end

local function fsExpandTraverse(root: roblox.Instance, path: string)
    local writeScriptTo

    if root:IsA("ModuleScript") then
        writeScriptTo = `{root.Name}.luau`
    elseif root:IsA("LocalScript") then
        writeScriptTo = `{root.Name}.client.luau`
    elseif root:IsA("Script") then
        local castRoot: any = root
        if castRoot.RunContext == 2 then
            writeScriptTo = `{root.Name}.client.luau`
        else
            writeScriptTo = `{root.Name}.server.luau`
        end
    end

    if writeScriptTo then
        local castRoot: any = root
        pcall(fs.writeDir, path)
        local writePath = path .. writeScriptTo
        writePath = string.gsub(writePath, ">", "_")
        writePath = string.gsub(writePath, "<", "_")
        fs.writeFile(writePath, castRoot.Source)
    end

    for _, child in root:GetChildren() do
        local name = root.Name

        if root:IsA("DataModel") then
            name = "scripts"
        end

        fsExpandTraverse(child, `{path}{name}/`)
    end
end

if fs_expand then
    print(`fs_expand mode enabled, traversing game tree...`)
    
    local rootPath = getDir(input)

    fsExpandTraverse(game, rootPath)
end

print("Done")
