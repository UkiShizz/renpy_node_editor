# RenPy Node Editor

Desktop editor for creating Ren'Py scripts through a visual node graph. Instead of manually writing code — simply place blocks (dialogs, menus, transitions) and connect them with lines.

## Key Features

- **Visual scene editor**: create game logic as a graph with nodes (blocks) and connections
- **Diverse block types**: SAY, MENU, IF, JUMP, CALL, SCENE, SHOW, MUSIC, SOUND, and many more
- **Parameter editor**: interactive editing of block parameters directly in the interface (auto-save)
- **Real-time code generation**: automatic conversion of the graph into a ready script.rpy with preview
- **Export to Ren'Py**: export the generated code to a Ren'Py project
- **Project saving**: export and import projects in JSON format
- **Multiple scenes**: create multiple scenes (acts) in one project
- **Interface localization**: support for Russian and English languages
- **Settings persistence**: window size, panel proportions, and other settings are saved automatically

## Project Structure

```
renpy_node_editor/
├── src/
│   └── renpy_node_editor/
│       ├── core/           # Data models, code generator, settings
│       │   ├── generator/  # Ren'Py code generation
│       │   └── i18n/       # Localization files (ru.json, en.json)
│       ├── runner/         # Ren'Py SDK integration
│       └── ui/             # Graphical interface
│           ├── node_graph/ # Visual graph representation
│           └── block_*.py   # Block palette and editor
├── configs/                # Block type configuration
├── tests/                  # Tests
└── editor_config.json      # Editor configuration (created automatically)
```

## Quick Start

### Requirements

- Python 3.8+
- PySide6
- Ren'Py SDK (for running created projects)

### Installation

```bash
# Clone the repository
git clone https://github.com/UkiShizz/renpy_node_editor.git
cd renpy_node_editor

# Create a virtual environment
python -m venv .venv

# Activate the environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
python src/renpy_node_editor/app.py
```

## Editor Settings

On first launch, the program will automatically create an `editor_config.json` file in the project root, where all settings will be saved:

- Window size and position
- Window maximization state
- Panel proportions
- Selected interface language
- Other editor settings

All settings are saved automatically when the program is closed.

### Changing Settings

1. Click the **"Settings"** button in the top panel
2. In the settings dialog, you can change:
   - **Interface language**: Russian or English
   - **Grid display**: enable/disable grid on canvas
   - **Grid size**: grid cell size
   - **Show tooltips**: enable/disable popup tooltips
   - **Auto-center**: automatically center the graph on load

## User Guide

### Step 1: Creating a Project in Ren'Py

**IMPORTANT**: Before exporting code to a Ren'Py project, you must first create a new project through Ren'Py SDK.

1. Launch Ren'Py SDK (Launcher)
2. Click "Create New Project"
3. Enter the project name and select a folder for saving
4. Wait for the project to be created
5. **Remember the project folder path** — you'll need it for export

### Step 2: Creating a Project in the Editor

1. Launch RenPy Node Editor
2. Click the **"New Project"** button in the top panel
3. Enter the project name
4. The project is created in memory — the save folder will be requested on first save

After creating the project, you'll see:
- **Center**: canvas for working with scenes
- **Left**: code preview panel (hidden by default)
- **Right**: block palette, scene management, and properties editor

### Step 3: Working with Scenes

A project can contain multiple scenes (acts). Each scene is a separate block graph.

#### Creating a New Scene

1. In the right panel, find the **"Scene Management"** section
2. Click the **"Add Scene"** button
3. Enter the scene name (e.g., "Act 1", "Prologue")
4. The new scene will appear in the list and become active

#### Switching Between Scenes

- Click on the scene name in the scene list
- The active scene is displayed on the canvas

#### Deleting a Scene

- Select the scene in the list
- Click the **"Delete Scene"** button

### Step 4: Adding Blocks

1. In the right panel, find the **block palette**
2. Blocks are grouped by categories:
   - **Flow**: START, LABEL, JUMP, CALL, RETURN
   - **Dialogue**: SAY, NARRATION
   - **Visual**: SCENE, SHOW, HIDE, IMAGE
   - **Logic**: IF, MENU, WHILE, FOR
   - **Audio**: MUSIC, SOUND, STOP_MUSIC
   - **Variables**: SET_VAR, DEFAULT, DEFINE
   - **Characters**: CHARACTER
   - And more...

3. **Drag** the desired block from the palette onto the canvas
4. The block will appear on the canvas where you dropped it

### Step 5: Editing Blocks

1. **Click** on a block on the canvas
2. The **properties editor** (Properties Panel) will open in the right panel
3. Fill in the block parameters:
   - For **SAY**: select a character and enter text
   - For **SCENE**: select a background image
   - For **JUMP/CALL**: select a label from the dropdown list
   - And so on...
4. **Changes are saved automatically** when editing

#### Editing Features:

- **JUMP and CALL blocks**: have a dropdown list with all labels from all scenes in the project
- **SAY blocks**: automatically detect characters from the project
- **Images and audio**: can select files through a file selection dialog
- **CHARACTER blocks**: allow setting internal name and display name for characters

### Step 6: Connecting Blocks

Blocks are connected with lines to create an execution flow.

1. **Hover** over a block's output port (right side of the block, golden circle)
2. **Hold the left mouse button** and drag
3. **Release** on another block's input port (left side, blue circle)
4. A connection will appear as a smooth curved line

#### Connection Rules:

- Blocks execute **top to bottom** in the order of connections
- For **sequential chains**: one output → one input
- For **parallel branches**: one output → multiple inputs (e.g., for IF block)
- For **merge points**: multiple outputs → one input

#### Deleting a Connection:

- **Click** on a connection (line) — it will be highlighted
- Press the **Delete** or **Backspace** key

#### Deleting Blocks:

- **Click** on a block — it will be highlighted
- Press the **Delete** or **Backspace** key
- All connections to this block will be automatically deleted

### Step 7: START Blocks and Labels

**START block** is the entry point into a scene. Each scene should have at least one START block.

1. Add a **START** block to the canvas
2. In the properties editor, enter the **label name** (e.g., "first", "second", "start")
3. Connect the START block to other blocks

**Important:**
- START blocks generate `label` in Ren'Py code
- Labels from START blocks are available for JUMP and CALL blocks
- At the beginning of the script, `label start:` is automatically created, which jumps to the first START block (if it exists)
- JUMP and CALL blocks are only generated if the target label exists

### Step 8: Viewing Generated Code

Code is generated automatically in real-time with any changes to the graph.

1. Click the **"Show Preview"** button in the top panel (or use the hotkey)
2. The preview panel will open with the generated Ren'Py code
3. The code updates automatically when blocks, connections, or properties are changed
4. You can copy the code or review it before export

### Step 9: Saving the Project

The editor project must be saved manually:

1. Click the **"Save"** button in the top panel
   - The button is only active if there are unsaved changes
2. If the project hasn't been saved yet, select a folder for saving
3. The project is saved in JSON format (file `project.json`) in the selected folder

**Important**: The editor project folder is separate from the Ren'Py project folder. The editor project contains only the visual graph, while export to Ren'Py creates or updates the `script.rpy` file in the Ren'Py project.

### Step 10: Exporting to Ren'Py Project

**IMPORTANT**: Make sure you have already created a Ren'Py project through Ren'Py SDK (see Step 1).

1. Click the **"Export to Ren'Py"** button in the top panel
2. In the dialog, select the **Ren'Py project folder** (not the `game` folder, but the root project folder)
   - For example: `C:\Users\YourName\Documents\RenPy\MyGame\`
   - Don't select: `C:\Users\YourName\Documents\RenPy\MyGame\game\`
3. Click "Select Folder"
4. If an existing Ren'Py project is selected:
   - The editor will warn that the `script.rpy` file will be replaced
   - Confirm the replacement
5. The editor will:
   - Create or update the `script.rpy` file in the `game/` folder
   - Copy image and audio files to the appropriate folders
   - Convert absolute paths to relative paths
   - Automatically detect and define characters, images, and other resources

**If the Ren'Py project doesn't exist:**
- The editor will create a basic project structure
- But it's recommended to first create a project through Ren'Py SDK for proper setup

### Step 11: Running the Project

After export, launch the project manually:

1. Open Ren'Py SDK (Launcher)
2. Find your project in the project list
3. Click **"Launch Project"** to run the game

## Block Types

### Script Structure

| Block | Description | Parameters |
|-------|-------------|------------|
| **START** | Scene entry point, generates a label | `label` - label name |
| **LABEL** | Creates a label for transitions | `label` - label name |
| **RETURN** | Return from function/scene | - |

### Dialogue and Text

| Block | Description | Parameters |
|-------|-------------|------------|
| **SAY** | Character dialogue | `character` - character, `text` - text |
| **NARRATION** | Narration (text without character) | `text` - text |

### Visual Elements

| Block | Description | Parameters |
|-------|-------------|------------|
| **SCENE** | Background change | `background` - background image, `layer`, `transition` |
| **SHOW** | Show character/image | `image` - image, `at`, `with` |
| **HIDE** | Hide character/image | `image` - image, `with` |
| **IMAGE** | Image definition | `name` - name, `file` - file path |

### Game Logic

| Block | Description | Parameters |
|-------|-------------|------------|
| **MENU** | Player choice menu | `prompt` - question text, `options` - answer options |
| **IF** | Conditional branching | `condition` - condition |
| **WHILE** | While loop | `condition` - condition |
| **FOR** | For loop | `variable` - variable, `iterable` - iterable object |
| **JUMP** | Jump to another label | `label` - label name (dropdown list) |
| **CALL** | Call another scene | `label` - label name (dropdown list) |

### Effects and Pauses

| Block | Description | Parameters |
|-------|-------------|------------|
| **PAUSE** | Pause in script | `duration` - duration in seconds |
| **TRANSITION** | Transition between scenes | `transition` - transition type, `duration` |
| **WITH** | Apply transition | `transition` - transition type |

### Audio

| Block | Description | Parameters |
|-------|-------------|------------|
| **MUSIC** | Background music | `music_file` - file path, `loop` - looping |
| **SOUND** | Sound effects | `sound_file` - file path |
| **STOP_MUSIC** | Stop music | `fadeout` - fadeout time |
| **STOP_SOUND** | Stop sound | - |
| **VOICE** | Voice line | `voice_file` - file path |

### Variables and Data

| Block | Description | Parameters |
|-------|-------------|------------|
| **SET_VAR** | Set variable | `variable` - variable name, `value` - value |
| **DEFAULT** | Default value | `variable` - variable name, `value` - value |
| **DEFINE** | Constant definition | `name` - name, `value` - value |
| **PYTHON** | Execute Python code | `code` - Python code |

### Characters and Definitions

| Block | Description | Parameters |
|-------|-------------|------------|
| **CHARACTER** | Character definition | `name` - internal name, `display_name` - display name, `color` - color |

## Tips and Recommendations

### Project Organization

- Use **multiple scenes** for different acts or chapters of the game
- Each scene should have **at least one START block** with a unique label
- Use **meaningful names** for labels (e.g., "prologue", "chapter1", "ending")

### Working with Images

- Add images through the **IMAGE** block before using them
- Use the **CHARACTER** block to define characters
- File paths are automatically converted to relative paths on export

### Working with Labels and Transitions

- **JUMP** — unconditional transition (doesn't return)
- **CALL** — scene call (returns via RETURN)
- Labels from all scenes are available in the JUMP/CALL block dropdown list
- JUMP and CALL blocks are only generated if the target label exists

### Debugging

- Use the **code preview panel** to check the generated code in real-time
- Check the console for errors during generation
- Make sure all file paths are correct

### Interface

- **Selecting blocks**: click on a block to select it
- **Selecting connections**: click on a connection line to select it
- **Deleting**: select an element and press Delete/Backspace
- **Moving blocks**: drag a block with the mouse
- **Changing panel proportions**: drag the divider between panels

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Adding New Block Types

1. Edit `configs/blocks_schema.json` — add a new type
2. Update `BlockType` in `core/model.py`
3. Add code generator in `core/generator/blocks.py`
4. Add UI logic in `ui/block_properties_panel.py`

## Architecture

- **Model** (`core/model.py`): data structures for project, scene, blocks
- **Controller** (`app_controller.py`): business logic for working with projects
- **View** (`ui/`): all UI components on PySide6
- **Runner** (`runner/`): Ren'Py integration for generation and running
- **Generator** (`core/generator/`): Ren'Py code generation from model
- **Settings** (`core/settings.py`): editor settings management
- **i18n** (`core/i18n.py`): interface localization system

## License

MIT

## Contact

If you find bugs or have ideas — create issues on GitHub.
